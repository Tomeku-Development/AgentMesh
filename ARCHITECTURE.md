# MESH Architecture

## Overview

MESH is a decentralized multi-agent supply chain coordination system. There is **no central orchestrator**. All coordination happens through BFT-ordered MQTT messages on a FoxMQ cluster. Because FoxMQ uses Hashgraph consensus, every agent sees messages in the same total order, making all local state computations (ledger balances, reputation scores, order states) converge deterministically.

## System Layers

```
+-----------------------------------------------------------+
|                    Dashboard (SvelteKit)                   |
+-----------------------------------------------------------+
|                WebSocket Bridge (Python)                   |
+-----------------------------------------------------------+
|                                                           |
|  +----------+  +----------+  +----------+  +----------+  |
|  |  Buyer   |  | Supplier |  | Logistics|  | Inspector|  |
|  +----------+  +----------+  +----------+  +----------+  |
|  |                  BaseAgent ABC                      |  |
|  |  Identity | State | Registry | Ledger | Reputation  |  |
|  +----------------------------------------------------+  |
|                                                           |
|  +----------------------------------------------------+  |
|  |  Negotiation Engine  |  Self-Healing  |  Arbiter    |  |
|  +----------------------------------------------------+  |
|                                                           |
+-----------------------------------------------------------+
|               FoxMQ BFT MQTT Cluster (4 nodes)            |
|               Hashgraph Gossip | MQTT 5.0                 |
+-----------------------------------------------------------+
```

## Layer 1: FoxMQ BFT Cluster

### What it provides
- **Total ordering**: All agents see messages in identical order
- **Byzantine fault tolerance**: Tolerates f < n/3 faulty nodes (1 of 4)
- **MQTT 5.0**: Standard pub/sub with QoS 0/1/2, retained messages, wildcards
- **Sub-100ms latency**: Hashgraph gossip protocol

### Cluster topology
4 FoxMQ nodes form the consensus cluster. Each agent connects to one node; the cluster replicates and orders all messages internally.

```
foxmq-node1 (port 1883) <--> foxmq-node2 (port 1884)
     ^                            ^
     |                            |
     v                            v
foxmq-node4 (port 1886) <--> foxmq-node3 (port 1885)
```

Agents are spread across nodes for fault isolation:
- Node 1: buyer, inspector, bridge
- Node 2: supplier_a, oracle
- Node 3: supplier_b
- Node 4: logistics

## Layer 2: Core Framework

### Identity (`core/identity.py`)
Each agent generates an Ed25519 keypair. The `agent_id` is the first 16 hex characters of `SHA-256(public_key_bytes)`. This provides:
- Unique, collision-resistant identifiers
- Cryptographic proof of identity
- Deterministic derivation from seed (for reproducible demos)

### Hybrid Logical Clocks (`core/clock.py`)
HLC combines physical wall-clock time with a logical counter. Format: `physical_ms:logical:node_id`. This ensures causal ordering even when wall clocks diverge between agents.

Operations:
- **tick()**: Local event -- advance physical time or increment logical counter
- **receive(remote)**: Merge remote HLC with local state, ensuring monotonicity

### Message Signing (`core/crypto.py`)
All message envelopes are signed with HMAC-SHA256 over canonical JSON (sorted keys, no whitespace). The shared secret is `mesh-vertex-swarm-2026` for the hackathon. In production, this would be derived from ECDH key exchange.

Additional protections:
- **ReplayDetector**: Bounded nonce cache (10,000 entries) prevents message replay
- **Freshness check**: Messages older than 60 seconds are rejected

### Message Models (`core/messages.py`)
22 Pydantic models define every message type:

| Category | Models |
|----------|--------|
| Envelope | `MessageHeader`, `MessageEnvelope` |
| Discovery | `DiscoveryAnnounce`, `Heartbeat`, `Goodbye` |
| Orders | `PurchaseOrderRequest`, `SupplierBid`, `CounterOffer`, `BidAcceptance`, `BidRejection`, `OrderCommit`, `OrderStatus` |
| Shipping | `ShippingRequest`, `ShippingBid`, `ShippingAssign`, `TransitUpdate` |
| Quality | `InspectionRequest`, `InspectionReport` |
| Market | `MarketPriceUpdate`, `MarketDemand` |
| Reputation | `ReputationUpdate` |
| Ledger | `LedgerTransaction` |
| Health | `HealthAlert`, `RoleRedistribution` |

### Agent State Machine (`core/state.py`)
8 states with validated transitions:

```
IDLE --> ACTIVE --> BUSY --> ACTIVE
           |                   |
           v                   v
        DEGRADED --> ACTIVE  SHUTDOWN
           |
        SHUTDOWN

(Peer view):
ACTIVE --> SUSPECT --> DEAD --> REJOINING --> ACTIVE
```

### Peer Registry (`core/registry.py`)
Every agent maintains a local registry of known peers, updated from MQTT discovery messages. Key features:
- **Liveness detection**: Peers transition ACTIVE -> SUSPECT -> DEAD based on heartbeat age
- **Role/capability filtering**: `get_by_role()`, `get_by_capability()`
- **Coordinator selection**: `longest_uptime_peer` returns the active peer with the earliest `first_seen` timestamp

### Ledger (`core/ledger.py`)
Deterministic double-entry ledger. Because all agents process the same BFT-ordered transaction stream, every ledger instance converges to the same state.

Operations:
- `transfer(from, to, amount, type)` -- Direct credit transfer
- `escrow_lock(from, amount, order_id)` -- Lock funds for an order
- `escrow_release(order_id, distributions)` -- Release to multiple recipients
- `escrow_refund(order_id)` -- Full refund to depositor

Burn address: `__burned__` -- credits transferred here are destroyed (3% deflationary burn on settlement).

### Reputation Engine (`core/reputation.py`)
Per-capability scoring (not global reputation). Each agent has a `CapabilityScore` for each skill.

Score range: 0.0 to 1.0, starting at 0.5 (neutral).

| Event | Delta |
|-------|-------|
| Successful fulfillment | +0.05 |
| On-time delivery | +0.03 |
| High quality (> 0.9) | +0.02 |
| Late delivery | -0.04 |
| Quality failure | -0.08 |
| No-show | -0.15 |
| Byzantine behavior | -0.25 |
| Epoch decay | toward 0.5 (factor 0.98) |

Confidence grows with each observation (+0.05 per transaction, capped at 1.0). The `score_bid()` method combines price (35%), reputation (30%), speed (20%), and confidence (15%) for weighted bid evaluation.

## Layer 3: Negotiation Engine

### State Machine

```
COLLECTING_BIDS --> EVALUATING --> COUNTERING --> AWAITING_RESPONSE
                       |              |                  |
                       v              v                  v
                   ACCEPTED       ACCEPTED           ACCEPTED
                       |              |                  |
                   REJECTED       TIMED_OUT          REJECTED
```

### Strategies

Three pluggable strategies compute counter-offer prices:

| Strategy | Buyer behavior | Supplier behavior |
|----------|---------------|-------------------|
| **Aggressive** | Push 40% toward 90% of market price | Give minimal 5% discount |
| **Conservative** | 5-10% below their price, shrinking per round | 3% discount |
| **Adaptive** | 5-15% discount based on competition + round pressure | 2-8% based on competition |

### Decision flow
1. Buyer publishes `PurchaseOrderRequest`
2. Suppliers submit `SupplierBid` within `bid_window`
3. Engine calls `evaluate_bids()` -- scores all bids
4. If best bid is < 95% of market price: accept immediately
5. If best bid is within budget but improvable: generate counter-offer
6. Up to `max_rounds` (default 3) counter-offer rounds
7. On acceptance: buyer locks escrow, supplier commits

### Dispute Resolution (Arbiter)
Deterministic rules applied after quality inspection:

- **Quality >= threshold**: Accepted
- **Quality >= 80% of threshold**: Partial refund (proportional to defect count)
- **Quality < 80% of threshold**: Full refund
- **Late delivery tiers**: <10% late = 2% penalty, 10-25% = 5%, >25% = 10%
- **No-show**: Severe reputation slash (-0.15)

## Layer 4: Self-Healing

### Failure Detection
Each agent runs a `FailureDetector` that monitors the `PeerRegistry`:

```
Heartbeat interval: 5s
Suspect threshold: 15s (3 missed)
Dead threshold: 30s (6 missed)
```

### Quorum Confirmation
A single agent's detection is not sufficient. Death is confirmed when >= 2 independent agents publish `HealthAlert` with severity `critical` for the same peer. This prevents false positives from network partitions.

### Role Redistribution
The `RoleRedistributor` runs on every agent. The coordinator (longest-uptime active peer) computes reassignments:
1. Identify the failed agent's active orders and capabilities
2. Find active peers with matching capabilities
3. Assign orders to the least-loaded compatible peer
4. Publish `RoleRedistribution` message

### Recovery
When a dead agent comes back:
1. It re-announces with status `rejoining`
2. Syncs ledger/reputation from retained MQTT messages
3. The `RecoveryManager` limits its load to 50% capacity for 2 epochs
4. After 2 epochs, transitions to full `ACTIVE` state

## Layer 5: Dashboard + Bridge

### WebSocket Bridge (`bridge/`)
A Python process subscribes to `mesh/#` (all topics) via MQTT and forwards messages to WebSocket clients. The `filters.py` module categorizes messages by type for the dashboard.

### SvelteKit Dashboard (`dashboard/`)
Real-time visualization with 5 components:

| Component | Shows |
|-----------|-------|
| **AgentCard** | Per-agent status, role, capabilities, load, state |
| **OrderFlow** | Order pipeline progression through phases |
| **MetricsPanel** | Ledger balances, transaction counts, reputation scores |
| **EventLog** | Scrolling log of all MQTT messages with timestamps |
| **ChaosControls** | Buttons to trigger agent kills/restarts during demo |

Stores use Svelte's reactive stores backed by the WebSocket connection.

## Data Flow: Complete Order Lifecycle

```
1. Oracle publishes market prices       mesh/market/prices
2. Buyer publishes purchase order       mesh/orders/{id}/request
3. Suppliers submit bids                mesh/orders/{id}/bid
4. Buyer evaluates + counters           mesh/orders/{id}/counter
5. Supplier accepts counter             mesh/orders/{id}/accept
6. Buyer locks escrow                   mesh/ledger/escrow
7. Supplier commits                     mesh/orders/{id}/commit
8. Buyer requests shipping              mesh/shipping/{id}/request
9. Logistics bids + assigned            mesh/shipping/{id}/bid, assign
10. Logistics picks up + transits       mesh/shipping/{id}/transit
11. Logistics delivers                  mesh/shipping/{id}/deliver
12. Buyer requests inspection           mesh/quality/{id}/request
13. Inspector submits report            mesh/quality/{id}/report
14. Arbiter resolves any disputes       (local computation)
15. Escrow released to participants     mesh/ledger/transactions
16. Reputation updated                  mesh/reputation/updates
```

## Performance

Benchmarks on Apple Silicon (single-threaded):

| Operation | Latency | Throughput |
|-----------|---------|------------|
| Canonical JSON | 0.001 ms | 762K ops/sec |
| HMAC-SHA256 sign | 0.002 ms | 500K ops/sec |
| Envelope build + sign | 0.010 ms | 103K ops/sec |
| Bid scoring | 0.001 ms | 1M+ ops/sec |
| Full negotiation cycle | 0.004 ms | 261K ops/sec |
| Escrow lock + release | 0.008 ms | 125K ops/sec |

All agent-local operations are sub-millisecond. The bottleneck in production is FoxMQ consensus latency (~50-100ms), not computation.

## Security Model

| Mechanism | Protection |
|-----------|-----------|
| Ed25519 identity | Agent impersonation |
| HMAC-SHA256 envelope signing | Message tampering |
| Replay detector (nonce cache) | Message replay attacks |
| Message freshness (60s window) | Stale message injection |
| BFT consensus (FoxMQ) | Byzantine broker nodes |
| Escrow mechanism | Payment fraud |
| Per-capability reputation | Sybil attacks (costly to build rep) |
| Quorum-based failure detection | False positive kills |

## Testing Strategy

| Suite | Count | Focus |
|-------|-------|-------|
| Unit | 100 | Individual components in isolation |
| Integration | 31 | Cross-component workflows (discovery, orders, settlement) |
| Chaos | 21 | Failure injection, recovery, redistribution |
| **Total** | **152** | **All passing in ~0.10s** |

Tests run without a live MQTT broker by testing the agent logic layer directly. The `PeerRegistry`, `Ledger`, `ReputationEngine`, and `NegotiationEngine` are all pure in-memory structures.
