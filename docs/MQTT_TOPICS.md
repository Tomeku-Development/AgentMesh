# MQTT Topics Reference

All MESH communication flows through MQTT topics on the FoxMQ BFT cluster. Topics use the `mesh/` prefix and are organized by domain.

## Topic Hierarchy

```
mesh/
|-- discovery/
|   |-- announce          Retained agent presence (QoS 1)
|   |-- heartbeat         Periodic liveness signal (QoS 0)
|   +-- goodbye           Graceful shutdown (QoS 1)
|
|-- orders/{order_id}/
|   |-- request           Purchase order published by buyer (QoS 1)
|   |-- bid               Supplier bids (QoS 1)
|   |-- counter           Counter-offers during negotiation (QoS 1)
|   |-- accept            Bid acceptance (QoS 1)
|   |-- reject            Bid rejection (QoS 1)
|   |-- commit            Supplier commitment confirmation (QoS 2)
|   +-- status            Order status updates (QoS 1)
|
|-- shipping/{shipment_id}/
|   |-- request           Shipping quote request (QoS 1)
|   |-- bid               Logistics provider bids (QoS 1)
|   |-- assign            Shipping task assignment (QoS 1)
|   |-- transit           In-transit status updates (QoS 0)
|   |-- deliver           Delivery confirmation (QoS 1)
|   +-- confirm           Buyer confirms receipt (QoS 1)
|
|-- quality/{inspection_id}/
|   |-- request           Inspection request (QoS 1)
|   |-- report            Inspection results (QoS 2)
|   +-- dispute           Quality dispute (QoS 2)
|
|-- market/
|   |-- prices            Oracle market price updates (QoS 1)
|   |-- demand            Oracle demand forecasts (QoS 1)
|   +-- alerts            Market alerts (QoS 1)
|
|-- reputation/
|   |-- scores            Full reputation snapshots (QoS 2)
|   +-- updates           Individual score changes (QoS 2)
|
|-- ledger/
|   |-- balances          Balance snapshots (QoS 2)
|   |-- transactions      Transaction records (QoS 2)
|   +-- escrow            Escrow lock/release events (QoS 2)
|
|-- health/
|   |-- alerts            Failure detection alerts (QoS 1)
|   |-- redistribution    Role reassignment messages (QoS 2)
|   +-- recovery          Recovery status updates (QoS 1)
|
|-- system/
|   +-- metrics           System-wide metrics (QoS 0)
|
+-- # (wildcard)          Used by bridge to capture all messages
```

## QoS Levels

| QoS | Usage | Topics |
|-----|-------|--------|
| **0** (Fire and forget) | High-frequency, loss-tolerant | `heartbeat`, `transit`, `metrics` |
| **1** (At least once) | Important but idempotent | `bid`, `request`, `status`, `alerts` |
| **2** (Exactly once) | Critical state changes | `commit`, `reputation`, `ledger`, `report` |

The QoS level is determined by `topics.qos_for_topic(topic)`:
- Topics containing `heartbeat` or `transit` -> QoS 0
- Topics containing `commit`, `settlement`, `reputation`, or `ledger` -> QoS 2
- Everything else -> QoS 1

## Topic Details

### Discovery Topics

#### `mesh/discovery/announce`
**Publisher**: All agents on startup and reconnect
**Subscribers**: All agents
**QoS**: 1 | **Retained**: Yes

Payload: `DiscoveryAnnounce`
```json
{
  "agent_id": "a1b2c3d4e5f67890",
  "role": "supplier",
  "capabilities": ["electronics", "displays", "keyboards"],
  "goods_categories": ["electronics"],
  "public_key_hex": "abcd1234...",
  "status": "online",
  "max_concurrent_orders": 5
}
```

#### `mesh/discovery/heartbeat`
**Publisher**: All agents (every `heartbeat_interval` seconds, default 5s)
**Subscribers**: All agents
**QoS**: 0 | **Retained**: No

Payload: `Heartbeat`
```json
{
  "agent_id": "a1b2c3d4e5f67890",
  "role": "supplier",
  "status": "healthy",
  "load": 0.4,
  "active_orders": 2,
  "uptime_seconds": 145.3
}
```

#### `mesh/discovery/goodbye`
**Publisher**: Agent shutting down
**Subscribers**: All agents
**QoS**: 1 | **Retained**: No

Payload: `Goodbye`
```json
{
  "agent_id": "a1b2c3d4e5f67890",
  "reason": "graceful_shutdown"
}
```

### Order Topics

#### `mesh/orders/{order_id}/request`
**Publisher**: Buyer
**Subscribers**: Suppliers (filtered by capabilities)

Payload: `PurchaseOrderRequest`
```json
{
  "order_id": "uuid",
  "goods": "laptop_display_15inch",
  "category": "electronics",
  "quantity": 50,
  "max_price_per_unit": 120.0,
  "quality_threshold": 0.85,
  "delivery_deadline_seconds": 60,
  "required_capabilities": ["electronics", "displays"],
  "bid_deadline_seconds": 10
}
```

#### `mesh/orders/{order_id}/bid`
**Publisher**: Suppliers
**Subscribers**: Buyer

Payload: `SupplierBid`
```json
{
  "order_id": "uuid",
  "bid_id": "uuid",
  "supplier_id": "a1b2c3d4e5f67890",
  "price_per_unit": 105.0,
  "available_quantity": 50,
  "estimated_fulfillment_seconds": 10,
  "reputation_score": 0.72,
  "notes": "In stock, ready to ship"
}
```

#### `mesh/orders/{order_id}/counter`
**Publisher**: Buyer or Supplier (alternating)
**Subscribers**: The other party

Payload: `CounterOffer`
```json
{
  "order_id": "uuid",
  "counter_id": "uuid",
  "original_bid_id": "uuid",
  "from_agent": "buyer_id",
  "to_agent": "supplier_id",
  "round": 1,
  "proposed_price_per_unit": 95.0,
  "proposed_quantity": 50,
  "proposed_deadline_seconds": null,
  "justification": "Market price is 100.00; round 1/3",
  "expires_seconds": 10
}
```

#### `mesh/orders/{order_id}/accept`
**Publisher**: Buyer
**Subscribers**: Accepted supplier

Payload: `BidAcceptance`
```json
{
  "order_id": "uuid",
  "accepted_bid_id": "uuid",
  "supplier_id": "a1b2c3d4e5f67890",
  "agreed_price_per_unit": 98.0,
  "agreed_quantity": 50,
  "escrow_amount": 4900.0,
  "escrow_tx_id": "uuid"
}
```

### Shipping Topics

#### `mesh/shipping/{shipment_id}/transit`
**Publisher**: Logistics agent
**Subscribers**: Buyer, supplier

Payload: `TransitUpdate`
```json
{
  "shipment_id": "uuid",
  "logistics_id": "logistics_agent_id",
  "status": "in_transit",
  "eta_seconds": 15,
  "condition": "good"
}
```

### Quality Topics

#### `mesh/quality/{inspection_id}/report`
**Publisher**: Inspector
**Subscribers**: Buyer, supplier

Payload: `InspectionReport`
```json
{
  "inspection_id": "uuid",
  "order_id": "uuid",
  "shipment_id": "uuid",
  "inspector_id": "inspector_agent_id",
  "quality_score": 0.92,
  "quantity_verified": 50,
  "quantity_defective": 0,
  "defect_descriptions": [],
  "passed": true,
  "recommendation": "accept"
}
```

### Health Topics

#### `mesh/health/alerts`
**Publisher**: Any agent's FailureDetector
**Subscribers**: All agents

Payload: `HealthAlert`
```json
{
  "detector_id": "detecting_agent_id",
  "suspect_agent_id": "failed_agent_id",
  "alert_type": "heartbeat_timeout",
  "severity": "critical",
  "missed_heartbeats": 6,
  "last_seen_seconds_ago": 32.5,
  "recommended_action": "redistribute"
}
```

#### `mesh/health/redistribution`
**Publisher**: Coordinator (longest-uptime peer)
**Subscribers**: All agents

Payload: `RoleRedistribution`
```json
{
  "redistribution_id": "uuid",
  "failed_agent_id": "dead_agent_id",
  "failed_role": "supplier",
  "replacement_agent_id": "backup_agent_id",
  "assumed_capabilities": ["electronics", "displays"],
  "active_orders_transferred": ["order_001", "order_002"]
}
```

## Message Envelope

Every MQTT message is wrapped in a `MessageEnvelope`:

```json
{
  "header": {
    "message_id": "uuid",
    "timestamp": "2026-04-03T12:00:00+00:00",
    "sender_id": "a1b2c3d4e5f67890",
    "sender_role": "buyer",
    "protocol_version": "mesh/1.0",
    "hlc": "1712145600000:0:a1b2c3d4e5f67890"
  },
  "payload": { ... },
  "signature": "hmac-sha256-hex-digest"
}
```

The signature is computed over the canonical JSON of `{"header": ..., "payload": ...}` using HMAC-SHA256.

## Subscribing by Role

| Agent Role | Subscribes To |
|------------|--------------|
| **All** | `discovery/announce`, `discovery/heartbeat`, `discovery/goodbye`, `health/alerts` |
| **Buyer** | `orders/+/bid`, `orders/+/counter`, `orders/+/commit`, `shipping/+/transit`, `quality/+/report`, `market/prices` |
| **Supplier** | `orders/+/request`, `orders/+/accept`, `orders/+/reject`, `orders/+/counter`, `market/prices` |
| **Logistics** | `shipping/+/request`, `shipping/+/assign` |
| **Inspector** | `quality/+/request` |
| **Oracle** | (publishes only: `market/prices`, `market/demand`) |
| **Bridge** | `mesh/#` (wildcard -- captures everything for dashboard) |
