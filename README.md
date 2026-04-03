# MESH -- Decentralized Multi-Agent Supply Chain Coordination

**Vertex Swarm Challenge 2026 -- Track 3: Agent Economy**

MESH is a fully decentralized multi-agent system where autonomous agents negotiate, trade, ship, inspect, and settle supply chain orders -- all without a central orchestrator. Agents coordinate exclusively through BFT-ordered MQTT messages on **Tashi Vertex / FoxMQ**, achieving consensus via Hashgraph gossip with sub-100ms latency.

```
                    FoxMQ BFT Cluster (4 nodes)
                   +-----------+-----------+
                   |  Hashgraph Consensus  |
                   +-----------+-----------+
                         |  MQTT 5.0
        +----------------+----------------+
        |        |        |        |      |
     Buyer   Supplier  Logistics Inspector Oracle
              (x2)
```

## Why MESH Wins

| Criterion | MESH |
|-----------|------|
| Multi-agent coordination | 5 distinct roles, pure P2P via BFT-ordered MQTT |
| Swarm intelligence | Adaptive negotiation strategies + per-capability reputation |
| Economic model | MESH_CREDIT currency, escrow, settlement splits, 3% burn |
| Resilience | Heartbeat failure detection, quorum confirmation, role redistribution, 50% capacity recovery ramp-up |
| Vertex integration | 4-node FoxMQ cluster, BFT ordering guarantees deterministic state convergence |
| Live demo | 3-minute scenario with supplier crash + self-healing recovery |

## Architecture

```
mesh/
  core/         Identity (Ed25519), HLC clocks, crypto, ledger, reputation, registry
  agents/       BaseAgent ABC + 5 role implementations
  negotiation/  Multi-round engine, 3 strategies, dispute arbiter
  healing/      Failure detection, role redistribution, recovery
  scenarios/    Scripted demo scenarios
bridge/         MQTT-to-WebSocket bridge for dashboard
dashboard/      SvelteKit real-time visualization
scripts/        Key generation, demo runner, benchmarks
tests/
  unit/         100 tests -- core + negotiation + reputation
  integration/  31 tests -- discovery, order lifecycle, settlement
  chaos/        21 tests -- self-healing, failure recovery
```

### Agent Roles

| Role | Responsibilities |
|------|-----------------|
| **Buyer** | Publishes purchase orders, evaluates bids, negotiates prices, locks escrow |
| **Supplier** | Bids on orders, fulfills committed orders, manages inventory and costs |
| **Logistics** | Bids on shipping requests, handles pickup/transit/delivery lifecycle |
| **Inspector** | Performs quality inspection, issues pass/partial/reject reports |
| **Oracle** | Publishes market prices and demand forecasts each epoch |

### Protocol Phases

```
DISCOVER --> REQUEST --> BID --> NEGOTIATE --> COMMIT --> EXECUTE --> VERIFY --> SETTLE
    |           |         |         |            |          |          |          |
 announce    publish   collect   counter     escrow     ship +     inspect    release
 + heartbeat  order     bids    (max 3)      lock      fulfill    quality    escrow
```

### Key Technical Decisions

- **No central orchestrator**: All coordination through FoxMQ-ordered MQTT topics
- **Deterministic state**: Same BFT-ordered messages = identical state on every agent
- **Ed25519 identity**: Each agent has a cryptographic keypair; agent_id = SHA-256(pubkey)[:16]
- **HMAC-SHA256 signing**: All message envelopes are signed and verified
- **Hybrid Logical Clocks**: Causal ordering across topics, even with clock skew
- **Per-capability reputation**: Score per skill (not global), decay toward neutral (0.5)
- **Pluggable negotiation**: Aggressive, Conservative, and Adaptive counter-offer strategies

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+ (for dashboard)
- Docker & Docker Compose (for full deployment)

### Install

```bash
# Python dependencies
cd mesh && pip install -e ".[dev]"

# Dashboard dependencies
cd dashboard && npm install
```

### Run Tests (152 passing)

```bash
# All tests
make test-unit && make test-int && make test-chaos

# Or directly with pytest
python -m pytest tests/ -v
```

### Generate Agent Keys

```bash
# Random keypairs
python scripts/generate_keys.py

# Deterministic (from seed strings)
python scripts/generate_keys.py --deterministic
```

### Run Benchmarks

```bash
python scripts/benchmark.py
```

Sample results (Apple Silicon):
```
canonical_json             0.0013 ms    762,000 ops/sec
envelope build + sign      0.0097 ms    103,000 ops/sec
full negotiation cycle     0.0038 ms    261,000 ops/sec
```

### Full Deployment (Docker)

```bash
# Start 4-node FoxMQ cluster + 6 agents + bridge + dashboard
docker compose up --build

# Dashboard at http://localhost:3000
# WebSocket bridge at ws://localhost:8080
```

### Run Demo Scenario

```bash
# Requires running FoxMQ cluster
make demo
```

The "Laptop Supply Chain" scenario runs for 3 minutes:
1. **t=8s**: Buyer orders 50 laptop displays (max $120/unit)
2. **t=50s**: Buyer orders 100 laptop batteries (max $50/unit)
3. **t=70s**: Supplier A crashes -- failure detected, roles redistributed
4. **t=100s**: Buyer orders 75 keyboards (max $30/unit)
5. **t=110s**: Supplier A recovers -- rejoins at 50% capacity for 2 epochs

## Economic Model

Currency: **MESH_CREDIT** (fiat-like, initialized per agent)

### Settlement Distribution

On successful order completion, escrowed funds are distributed:

| Recipient | Share | Purpose |
|-----------|-------|---------|
| Supplier | 92% | Goods payment |
| Logistics | 3% | Shipping fee |
| Inspector | 2% | Quality inspection fee |
| Burned | 3% | Deflationary mechanism |

### Dispute Resolution

The deterministic Arbiter resolves disputes based on inspection reports:

- **Quality >= threshold**: Accepted, no penalties
- **Quality >= 80% of threshold**: Partial refund proportional to defects, -0.08 reputation
- **Quality < 80% of threshold**: Full refund, -0.15 reputation slash
- **Late delivery**: 2-10% penalty depending on lateness ratio
- **No-show**: -0.15 reputation slash (byzantine-level)

## Self-Healing

```
Heartbeat miss --> SUSPECT (3 missed) --> DEAD (6 missed)
                                              |
                                    Quorum vote (>= 2 agents)
                                              |
                                    Role redistribution
                                              |
                                    Agent recovers --> REJOINING (50% load, 2 epochs)
                                              |
                                           ACTIVE
```

- **Detection**: Each agent runs a `FailureDetector` monitoring peer heartbeats
- **Confirmation**: Death requires quorum (>= 2 independent detectors agree)
- **Redistribution**: Longest-uptime active peer becomes coordinator, reassigns orders
- **Recovery**: Rejoining agents operate at 50% capacity for 2 epochs before full activation

## Project Structure

```
Project-Vertex/
|-- mesh/                     Python agent framework
|   |-- core/
|   |   |-- identity.py       Ed25519 keypair management
|   |   |-- crypto.py         HMAC-SHA256 signing, replay detection
|   |   |-- clock.py          Hybrid Logical Clocks
|   |   |-- config.py         Pydantic settings (env vars)
|   |   |-- messages.py       22 Pydantic message models
|   |   |-- protocol.py       Envelope build/verify/serialize
|   |   |-- topics.py         MQTT topic constants + QoS mapping
|   |   |-- state.py          Agent FSM (8 states, validated transitions)
|   |   |-- registry.py       Peer discovery registry
|   |   |-- ledger.py         Double-entry ledger with escrow
|   |   |-- reputation.py     Per-capability scoring engine
|   |   +-- transport.py      MQTT transport layer
|   |-- agents/
|   |   |-- base.py           BaseAgent ABC (lifecycle, heartbeat, dispatch)
|   |   |-- buyer.py          Purchase order + negotiation logic
|   |   |-- supplier.py       Bidding + fulfillment logic
|   |   |-- logistics.py      Shipping lifecycle management
|   |   |-- inspector.py      Quality inspection + reporting
|   |   +-- oracle.py         Market data publisher
|   |-- negotiation/
|   |   |-- strategies.py     Aggressive/Conservative/Adaptive
|   |   |-- engine.py         Multi-round state machine
|   |   +-- arbiter.py        Dispute resolution
|   |-- healing/
|   |   |-- detector.py       Heartbeat failure detection
|   |   |-- redistributor.py  Role reassignment
|   |   +-- recovery.py       Capacity ramp-up manager
|   |-- scenarios/
|   |   |-- base.py           Scenario framework
|   |   +-- electronics.py    "Laptop Supply Chain" demo
|   +-- cli.py                Click CLI entry point
|-- bridge/
|   |-- server.py             MQTT -> WebSocket bridge
|   +-- filters.py            Topic filtering for dashboard
|-- dashboard/                SvelteKit real-time UI
|   +-- src/
|       |-- routes/+page.svelte
|       +-- lib/
|           |-- components/   AgentCard, OrderFlow, MetricsPanel, EventLog, ChaosControls
|           +-- stores/       WebSocket, agents, orders, metrics
|-- scripts/
|   |-- generate_keys.py      Ed25519 keypair generation
|   |-- run_demo.py           Local demo scenario runner
|   +-- benchmark.py          Performance benchmarks
|-- tests/
|   |-- unit/                 100 tests
|   |-- integration/          31 tests
|   +-- chaos/                21 tests
|-- docker-compose.yml        Full stack: FoxMQ (4 nodes) + agents + bridge + dashboard
|-- Dockerfile.agent          Python agent container
|-- foxmq/                    FoxMQ broker build
|-- Makefile                  Build/test/deploy commands
+-- .env.example              Configuration template
```

## Configuration

All agent configuration via environment variables (prefix `MESH_`):

| Variable | Default | Description |
|----------|---------|-------------|
| `MESH_BROKER_HOST` | `127.0.0.1` | FoxMQ broker hostname |
| `MESH_BROKER_PORT` | `1883` | MQTT port |
| `MESH_AGENT_ROLE` | `buyer` | Agent role |
| `MESH_AGENT_ID` | `auto` | Agent ID (auto = derive from Ed25519 pubkey) |
| `MESH_CAPABILITIES` | `` | Comma-separated capabilities |
| `MESH_INITIAL_BALANCE` | `10000` | Starting MESH_CREDIT balance |
| `MESH_HEARTBEAT_INTERVAL` | `5.0` | Seconds between heartbeats |
| `MESH_NEGOTIATE_MAX_ROUNDS` | `3` | Max counter-offer rounds |
| `MESH_SCENARIO` | `electronics` | Demo scenario to run |

## Team

**Hitazurana** -- Vertex Swarm Challenge 2026

## License

MIT
