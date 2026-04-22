# MESH — Pitch Deck Documentation

**Vertex Swarm Challenge 2026 · Track 3: Agent Economy**

---

## The Problem

Global supply chains are fragile. They depend on centralized coordination platforms that create single points of failure, lack transparency between participants, and can't adapt in real-time when disruptions occur. When a supplier goes down or demand shifts unexpectedly, the entire chain stalls while humans scramble to reroute.

Existing multi-agent systems either rely on a central orchestrator (defeating the purpose of decentralization) or lack the economic incentives and trust mechanisms needed for autonomous agents to cooperate reliably.

---

## The Solution: MESH

MESH is a fully decentralized multi-agent supply chain coordination system where **5 autonomous agent roles** — Buyer, Supplier, Logistics, Inspector, and Oracle — negotiate, trade, ship, inspect, and settle orders with **zero central orchestration**.

Agents coordinate exclusively through **BFT-ordered MQTT messages** on Tashi Vertex / FoxMQ, achieving deterministic state convergence via Hashgraph consensus with sub-100ms latency. Every agent makes intelligent decisions powered by **LLM providers** (Amazon Bedrock + OpenRouter) with automatic fallback to deterministic heuristics.

The system ships as a **production-grade enterprise SaaS platform** — not just a research prototype.

---

## How It Works

```
    Buyer          Supplier (x2)      Logistics       Inspector       Oracle
      │                 │                 │               │              │
      ├── REQUEST ──────┤                 │               │              │
      │                 ├── BID ──────────┤               │              │
      ├── NEGOTIATE ────┤                 │               │              │
      ├── COMMIT ───────┤                 │               │              │
      │                 ├── EXECUTE ──────┤               │              │
      │                 │                 ├── VERIFY ─────┤              │
      ├── SETTLE ───────┤─────────────────┤───────────────┤              │
      │                 │                 │               │              │
                    All via BFT-ordered MQTT (FoxMQ Hashgraph)
```

**8-phase protocol**: DISCOVER → REQUEST → BID → NEGOTIATE → COMMIT → EXECUTE → VERIFY → SETTLE

Each phase is a cryptographically signed MQTT message. BFT ordering guarantees every agent sees the same sequence, producing identical state without any coordinator.

---

## Key Differentiators

### 1. True Decentralization
No central orchestrator, no message broker bottleneck. A 4-node FoxMQ Hashgraph cluster provides BFT consensus. Agents connect to any node and get the same deterministic ordering.

### 2. LLM-Powered Intelligence
11 specialized prompt templates drive agent decisions — from bid evaluation to dispute resolution to self-healing analysis. Circuit breaker pattern with multi-provider fallback (Bedrock → OpenRouter → deterministic heuristic) ensures agents never stop making decisions.

### 3. Self-Healing Resilience
When an agent fails, the system detects it via heartbeat monitoring, confirms death through quorum voting, redistributes its workload to capability-matched peers, and gracefully reintegrates the agent when it recovers — all autonomously.

### 4. Real Economic Model
MESH_CREDIT currency with double-entry ledger, escrow-based settlement, per-capability reputation scoring, and a 3% deflationary burn. Agents have real economic incentives to cooperate and real penalties for misbehavior.

### 5. Production SaaS Platform
Not a demo — a full enterprise control plane with multi-tenant workspaces, 6-role RBAC, analytics dashboards, SLA monitoring, webhook integrations, an agent marketplace, dual payment providers, and a published TypeScript SDK.

---

## Platform Capabilities

### Enterprise Control Plane

| Capability | Description |
|-----------|-------------|
| **Multi-Tenant Workspaces** | Isolated environments with slug-based MQTT topic namespacing |
| **6-Role RBAC** | Owner, Admin, Operator, Developer, Auditor, Viewer — with escalation prevention |
| **Agent Analytics** | Per-agent performance metrics, order lifecycle timelines, economic health dashboards |
| **Custom Scenarios** | Build and run custom supply chain simulations with configurable agents, goods, and chaos events |
| **SLA Monitoring** | Define performance thresholds, get alerted on breaches, acknowledge and track resolution |
| **Webhook Integrations** | HMAC-signed outbound notifications, retry with exponential backoff, inbound order triggers |
| **Agent Marketplace** | Register, discover, and instantiate reusable agent templates across workspaces |
| **Dual Payments** | Xendit (fiat: 5 currencies) + Cryptomus (crypto: 150+ tokens) |
| **TypeScript SDK** | Published npm package with CLI for building custom agents |
| **Real-Time Dashboard** | SvelteKit UI with D3 visualizations, live event streaming, chaos controls |

### API Surface

14 router groups serving 50+ REST endpoints under `/api/v1`, covering auth, workspaces, orders, ledger, agents, analytics, scenarios, SLA, webhooks, marketplace, payments, API keys, capabilities, and admin.

Full OpenAPI 3.0 spec + AsyncAPI 3.0 specs for MQTT and WebSocket protocols. Fern-generated documentation at [docs.agentmesh.world](https://docs.agentmesh.world).

---

## Technical Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     Dashboard (SvelteKit)                        │
│  Agent Cards · Order Flow · Metrics · Event Log · Chaos Controls│
├─────────────────────────────────────────────────────────────────┤
│                  WebSocket Gateway + Bridge                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐           │
│  │  Buyer   │ │ Supplier │ │ Logistics│ │ Inspector│  + Oracle  │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘           │
│  ┌──────────────────────────────────────────────────┐           │
│  │  BaseAgent ABC + LLM Router + Negotiation Engine  │           │
│  │  Identity · State · Ledger · Reputation · Healing │           │
│  └──────────────────────────────────────────────────┘           │
│                                                                  │
├─────────────────────────────────────────────────────────────────┤
│         FoxMQ BFT MQTT Cluster (4 nodes, Hashgraph)              │
├─────────────────────────────────────────────────────────────────┤
│                   SaaS Platform (FastAPI)                         │
│  Auth · RBAC · Analytics · Scenarios · SLA · Webhooks            │
│  Marketplace · Payments · Event Sink · PostgreSQL                 │
└─────────────────────────────────────────────────────────────────┘
```

### Tech Stack

| Layer | Technology |
|-------|-----------|
| Agent Framework | Python 3.11, Pydantic, paho-mqtt, PyNaCl, httpx |
| Consensus | FoxMQ (Hashgraph BFT), MQTT 5.0 |
| SaaS Platform | FastAPI, SQLAlchemy 2.0 (async), PostgreSQL, Alembic |
| Dashboard | SvelteKit, D3.js, Vite |
| SDK | TypeScript, WebSocket, npm package |
| LLM | Amazon Bedrock, OpenRouter (multi-provider with circuit breaker) |
| Payments | Xendit (fiat), Cryptomus (crypto) |
| Infrastructure | Docker Compose, 4-node FoxMQ cluster |

---

## Economic Model

### Currency: MESH_CREDIT

In-memory double-entry ledger with escrow. Every transaction is recorded, auditable, and deterministic.

### Settlement Split

| Recipient | Share |
|-----------|-------|
| Supplier | 92% |
| Logistics | 3% |
| Inspector | 2% |
| Burned (deflationary) | 3% |

### Reputation System

Per-capability scoring — agents build reputation per skill, not globally. Scores decay toward neutral (0.5) each epoch, preventing stale reputations.

Bid evaluation weights: **price 35%** · **reputation 30%** · **speed 20%** · **confidence 15%**

### Dispute Resolution

Deterministic arbiter with optional LLM analysis. Quality-based outcomes: full payment, partial refund, or full refund with reputation penalties.

---

## Testing & Quality

**292+ tests, all passing.** Comprehensive coverage across four test suites:

| Suite | Tests | Coverage |
|-------|-------|---------|
| Unit | 100 | Core components in isolation |
| Integration | 31 | Cross-component workflows |
| Chaos | 21 | Failure injection and recovery |
| Platform | 140 | API endpoints + 11 formal correctness properties |

### Formal Correctness Properties

Every platform feature is validated with **property-based testing** using Hypothesis (100+ iterations per property). Properties define what the system must always do, not just specific examples:

1. Analytics aggregation produces correct counts and sums for any dataset
2. Order timeline durations sum to total elapsed time for any event sequence
3. Webhook URLs are accepted if and only if they use HTTPS
4. Scenario definitions survive JSON round-trip serialization for any valid input
5. Invalid scenarios (missing buyer/supplier/goods) are always rejected
6. SLA breaches are detected if and only if the threshold condition holds
7. RBAC permissions match the defined role-to-access mapping for all role/level combinations
8. Self-escalation to a higher role is always rejected
9. Marketplace search results match filters and are ordered by popularity
10. Template instantiation correctly merges defaults with overrides
11. Template names are accepted if and only if they're 3-100 characters

---

## Live Demo

### "Laptop Supply Chain" Scenario (3 minutes)

| Time | Event |
|------|-------|
| t=0s | 6 agents boot, discover each other, Oracle publishes market prices |
| t=8s | Buyer orders 50 laptop displays (max $120/unit) |
| t=15s | Suppliers bid, negotiate, commit. Logistics ships. Inspector verifies. Settlement. |
| t=50s | Buyer orders 100 laptop batteries (max $50/unit) |
| t=70s | **Supplier A crashes** — failure detected via heartbeat, quorum confirms death |
| t=75s | Roles redistributed to Supplier B. Orders continue without interruption. |
| t=100s | Buyer orders 75 keyboards (max $30/unit) |
| t=110s | **Supplier A recovers** — rejoins at 50% capacity for 2 epochs, then full capacity |
| t=180s | Scenario complete. All orders settled. Ledger balanced. |

The demo showcases: multi-agent negotiation, LLM-powered decisions, escrow settlement, self-healing recovery, and real-time dashboard visualization.

### Performance

Benchmarked on Apple Silicon:

| Operation | Latency | Throughput |
|-----------|---------|-----------|
| Canonical JSON serialization | 0.0013 ms | 762,000 ops/sec |
| Envelope build + sign | 0.0097 ms | 103,000 ops/sec |
| Full negotiation cycle | 0.0038 ms | 261,000 ops/sec |

---

## Deployment

### Docker Compose (One Command)

```bash
# Full stack: FoxMQ cluster + agents + bridge + dashboard + PostgreSQL + API
docker compose -f docker-compose.yml -f docker-compose.saas.yml up --build
```

| Service | URL |
|---------|-----|
| Dashboard | http://localhost:3000 |
| Platform API | http://localhost:8000 |
| API Docs (Swagger) | http://localhost:8000/docs |
| WebSocket Bridge | ws://localhost:8080 |

### Production

- Live at [agentmesh.world](https://agentmesh.world)
- API docs at [docs.agentmesh.world](https://docs.agentmesh.world)
- SDK on npm: `@agentmeshworld/sdk`

---

## What Makes This Submission Stand Out

1. **Not a prototype** — a production SaaS platform with auth, billing, RBAC, analytics, and a published SDK
2. **Formally verified** — 11 correctness properties validated with property-based testing, not just example tests
3. **True BFT decentralization** — 4-node Hashgraph cluster, not a single broker pretending to be distributed
4. **LLM-native** — every agent decision can be LLM-powered, with graceful degradation to heuristics
5. **Self-healing** — autonomous failure detection, quorum confirmation, role redistribution, and recovery
6. **Complete economic model** — currency, escrow, settlement splits, reputation, dispute resolution, deflationary burn
7. **Developer-ready** — TypeScript SDK on npm, OpenAPI/AsyncAPI specs, Fern-generated docs, CLI tools
8. **292+ tests passing** — unit, integration, chaos, platform, and property-based test suites

---

## Team

**Hitazurana (HiroJei)** · [Tomeku Development](https://tomeku.com)

Vertex Swarm Challenge 2026 · Track 3: Agent Economy

---

## Links

- **Live Demo**: [agentmesh.world](https://agentmesh.world)
- **API Documentation**: [docs.agentmesh.world](https://docs.agentmesh.world)
- **TypeScript SDK**: [npm @agentmeshworld/sdk](https://www.npmjs.com/package/@agentmeshworld/sdk)
- **Dashboard**: [agentmesh.world/dashboard](https://agentmesh.world/dashboard)
