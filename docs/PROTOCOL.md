# MESH Protocol Specification

Version: `mesh/1.0`

## Overview

The MESH protocol defines how autonomous supply chain agents coordinate purchase orders from request to settlement. All messages are published to MQTT topics on a FoxMQ BFT cluster, ensuring total ordering and Byzantine fault tolerance.

## Protocol Phases

```
Phase 0: DISCOVER    (continuous)
Phase 1: REQUEST     Buyer publishes purchase order
Phase 2: BID         Suppliers submit competing bids
Phase 3: NEGOTIATE   Multi-round counter-offers (max 3 rounds)
Phase 4: COMMIT      Escrow lock + supplier commitment
Phase 5: EXECUTE     Fulfillment + shipping + transit
Phase 6: VERIFY      Quality inspection
Phase 7: SETTLE      Escrow release + reputation updates
```

---

## Phase 0: DISCOVER (continuous)

Discovery runs throughout the agent's lifetime, independent of any order.

### 0.1 Agent Announcement

On startup, each agent publishes a **retained** message:

```
Topic:   mesh/discovery/announce
QoS:     1
Retain:  true
Payload: DiscoveryAnnounce
```

Fields:
- `agent_id`: 16-char hex identifier (SHA-256 of Ed25519 public key)
- `role`: One of `buyer`, `supplier`, `logistics`, `inspector`, `oracle`
- `capabilities`: List of skills (e.g., `["electronics", "displays"]`)
- `public_key_hex`: Full Ed25519 public key for identity verification
- `status`: One of `online`, `busy`, `degraded`, `rejoining`

### 0.2 Heartbeat

Every `heartbeat_interval` seconds (default 5s):

```
Topic:   mesh/discovery/heartbeat
QoS:     0
Payload: Heartbeat
```

Fields:
- `status`: `healthy`, `busy`, or `degraded`
- `load`: Float 0.0-1.0 (active_orders / max_concurrent)
- `active_orders`: Current number of in-progress orders
- `uptime_seconds`: Time since agent start

### 0.3 Goodbye

On graceful shutdown:

```
Topic:   mesh/discovery/goodbye
QoS:     1
Payload: Goodbye
```

### 0.4 Liveness Detection

Each agent locally monitors peer heartbeats:
- **SUSPECT**: No heartbeat for `suspect_threshold` seconds (default 15s = 3 missed)
- **DEAD**: No heartbeat for `dead_threshold` seconds (default 30s = 6 missed)

State transitions are tracked in the local `PeerRegistry`.

---

## Phase 1: REQUEST

The buyer identifies a need and publishes a purchase order.

### 1.1 Purchase Order

```
Topic:   mesh/orders/{order_id}/request
QoS:     1
Payload: PurchaseOrderRequest
```

Fields:
- `order_id`: Unique UUID for this order
- `goods`: Product identifier (e.g., `"laptop_display_15inch"`)
- `category`: Product category for capability matching (e.g., `"electronics"`)
- `quantity`: Number of units requested
- `max_price_per_unit`: Maximum price the buyer will pay
- `quality_threshold`: Minimum quality score (0.0-1.0, typically 0.85)
- `delivery_deadline_seconds`: Maximum time for fulfillment + shipping
- `required_capabilities`: Capabilities suppliers must have
- `bid_deadline_seconds`: Time window for collecting bids (default 10s)

### 1.2 Order State

The buyer sets local order state to `bidding` and starts the bid collection timer.

---

## Phase 2: BID

Suppliers with matching capabilities submit bids.

### 2.1 Supplier Bid

```
Topic:   mesh/orders/{order_id}/bid
QoS:     1
Payload: SupplierBid
```

Fields:
- `supplier_id`: Bidding supplier's agent ID
- `price_per_unit`: Offered price
- `available_quantity`: Units the supplier can provide
- `estimated_fulfillment_seconds`: Time to prepare goods
- `reputation_score`: Supplier's self-reported reputation (verified by buyer)

### 2.2 Bid Evaluation

After `bid_deadline_seconds` expires, the buyer's `NegotiationEngine` evaluates all collected bids:

**Scoring formula** (default weights):
```
score = 0.35 * price_score + 0.30 * reputation + 0.20 * speed_score + 0.15 * confidence
```

Where:
- `price_score = max(0, 1 - price/max_price)`
- `speed_score = max(0, 1 - estimated_time/deadline)`
- `reputation` and `confidence` from the `ReputationEngine`

**Decision logic**:
- If best bid price <= 95% of market price: **accept immediately** (skip Phase 3)
- If best bid price <= max_price: **counter** if rounds remaining
- If best bid price > max_price: **counter** if rounds remaining, else **reject**

---

## Phase 3: NEGOTIATE

Multi-round counter-offer exchange. Maximum `negotiate_max_rounds` (default 3).

### 3.1 Counter-Offer

```
Topic:   mesh/orders/{order_id}/counter
QoS:     1
Payload: CounterOffer
```

Fields:
- `original_bid_id`: Reference to the bid being countered
- `from_agent` / `to_agent`: Sender and recipient
- `round`: Current round number (1-indexed)
- `proposed_price_per_unit`: Counter-offer price
- `proposed_quantity`: Optional quantity adjustment
- `justification`: Human-readable explanation
- `expires_seconds`: Time for the other party to respond

### 3.2 Strategy Selection

The counter-offer price is computed by the selected `BiddingStrategy`:

| Strategy | Formula (buyer countering supplier's price P) |
|----------|-----------------------------------------------|
| **Aggressive** | `P - 0.4 * (P - market * 0.90)` |
| **Conservative** | `P * (1 - 0.05 - 0.05 * (1 - round/max_rounds))` |
| **Adaptive** | `P * (1 - base_discount + round_concession)` where `base = 0.05 + 0.10 * competition_factor` |

A floor of `market_price * 0.80` prevents unreasonable counter-offers.

### 3.3 Counter-Response

The supplier can:
1. **Accept** the counter-offer -> proceed to Phase 4
2. **Counter** with their own price -> another round (if rounds remain)
3. **Reject** -> negotiation fails, order cancelled or re-bid

### 3.4 Negotiation State Machine

```
COLLECTING_BIDS --[bid_deadline]--> EVALUATING
     |                                  |
     v                                  v
 (bids arrive)                  [evaluate_bids()]
                                   |         |
                            accept |         | should_counter
                                   v         v
                               ACCEPTED   COUNTERING --[generate_counter]--> AWAITING_RESPONSE
                                                                                    |
                                                            accepted?   +-----------+
                                                                |       |
                                                                v       v
                                                            ACCEPTED  (next round or REJECTED)
```

Constraints:
- `can_counter` requires state in `{EVALUATING, COUNTERING}` AND `current_round < max_rounds` AND not expired
- `evaluate_bids()` must be called before `generate_counter()` to transition state

---

## Phase 4: COMMIT

### 4.1 Bid Acceptance

```
Topic:   mesh/orders/{order_id}/accept
QoS:     1
Payload: BidAcceptance
```

The buyer:
1. Locks `agreed_price * quantity` in escrow via `Ledger.escrow_lock()`
2. Publishes acceptance with `escrow_tx_id`
3. Sets order state to `committed`

### 4.2 Supplier Commitment

```
Topic:   mesh/orders/{order_id}/commit
QoS:     2 (exactly once -- critical state change)
Payload: OrderCommit
```

The supplier confirms commitment and begins fulfillment.

### 4.3 Rejection (alternative)

```
Topic:   mesh/orders/{order_id}/reject
QoS:     1
Payload: BidRejection
```

Unsuccessful bidders receive explicit rejections.

---

## Phase 5: EXECUTE

### 5.1 Fulfillment

The supplier prepares the order (internal, no MQTT message).

### 5.2 Shipping Request

```
Topic:   mesh/shipping/{shipment_id}/request
QoS:     1
Payload: ShippingRequest
```

Published by the buyer (or supplier) after commitment.

### 5.3 Shipping Bid

```
Topic:   mesh/shipping/{shipment_id}/bid
QoS:     1
Payload: ShippingBid
```

Logistics agents bid on shipping tasks.

### 5.4 Shipping Assignment

```
Topic:   mesh/shipping/{shipment_id}/assign
QoS:     1
Payload: ShippingAssign
```

Best logistics bid is selected and assigned.

### 5.5 Transit Updates

```
Topic:   mesh/shipping/{shipment_id}/transit
QoS:     0 (high frequency, loss tolerant)
Payload: TransitUpdate
```

Status progression: `picked_up` -> `in_transit` -> `out_for_delivery` -> `delivered`

---

## Phase 6: VERIFY

### 6.1 Inspection Request

```
Topic:   mesh/quality/{inspection_id}/request
QoS:     1
Payload: InspectionRequest
```

After delivery, the buyer requests quality inspection.

### 6.2 Inspection Report

```
Topic:   mesh/quality/{inspection_id}/report
QoS:     2 (exactly once -- determines settlement)
Payload: InspectionReport
```

Fields:
- `quality_score`: 0.0-1.0 overall quality
- `quantity_verified` / `quantity_defective`: Unit counts
- `passed`: Boolean
- `recommendation`: `accept`, `partial_accept`, or `reject`

### 6.3 Dispute Resolution

If `quality_score < quality_threshold`, the deterministic `Arbiter` resolves:

| Condition | Outcome | Refund | Reputation |
|-----------|---------|--------|------------|
| `score >= threshold` | Accepted | 0% | No change |
| `score >= threshold * 0.8` | Partial refund | Proportional to defect ratio | -0.08 |
| `score < threshold * 0.8` | Full refund | 100% | -0.15 |

---

## Phase 7: SETTLE

### 7.1 Escrow Release

The buyer calls `Ledger.escrow_release()` with distribution:

```
distributions = [
    (supplier_id, total * 0.92, "Goods payment"),
    (logistics_id, total * 0.03, "Shipping fee"),
    (inspector_id, total * 0.02, "Inspection fee"),
    ("__burned__", total * 0.03, "Deflationary burn"),
]
```

If disputes reduce payment, the refund percentage is subtracted from the supplier's share.

### 7.2 Reputation Updates

```
Topic:   mesh/reputation/updates
QoS:     2
Payload: ReputationUpdate
```

Updates are published for all participants:
- **Supplier**: `record_success()` with `on_time` and `quality_score` flags
- **Logistics**: Success/failure based on delivery timing
- **Inspector**: Success for completing inspection

### 7.3 Ledger Broadcast

```
Topic:   mesh/ledger/transactions
QoS:     2
Payload: LedgerTransaction (one per distribution line)
```

---

## Self-Healing Protocol

### Health Alert Publication

When a `FailureDetector` detects a dead peer:

```
Topic:   mesh/health/alerts
QoS:     1
Payload: HealthAlert
```

### Quorum Vote

Each agent independently monitors heartbeats. When >= 2 agents publish `critical` alerts for the same peer, death is confirmed.

### Role Redistribution

The coordinator (longest-uptime active peer) publishes:

```
Topic:   mesh/health/redistribution
QoS:     2
Payload: RoleRedistribution
```

### Recovery Announcement

A recovering agent re-announces with `status: "rejoining"`:

```
Topic:   mesh/discovery/announce
Payload: DiscoveryAnnounce { status: "rejoining" }
```

The `RecoveryManager` limits load to 50% for `recovery_epochs` (default 2) before full activation.

---

## Envelope Format

Every MQTT message is wrapped in a `MessageEnvelope`:

```json
{
  "header": {
    "message_id": "UUID v4",
    "timestamp": "ISO 8601 UTC",
    "sender_id": "16-char hex agent ID",
    "sender_role": "buyer|supplier|logistics|inspector|oracle",
    "protocol_version": "mesh/1.0",
    "hlc": "physical_ms:logical:node_id"
  },
  "payload": { ... },
  "signature": "HMAC-SHA256 hex digest"
}
```

### Signature Computation

```python
signable = {"header": header_dict, "payload": payload_dict}
canonical = json.dumps(signable, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
signature = hmac.new(secret, canonical.encode("utf-8"), hashlib.sha256).hexdigest()
```

### Verification

On receipt, every agent:
1. Recomputes the signature from the received header + payload
2. Compares using constant-time `hmac.compare_digest()`
3. Drops messages with invalid signatures

### Causal Ordering

HLC timestamps ensure causal consistency:
- **Local event**: `tick()` advances physical time or increments logical counter
- **Remote event**: `receive(remote_hlc)` merges clocks, ensuring monotonicity
- **Comparison**: `(physical, logical, node_id)` total order
