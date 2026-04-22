<div align="center">

# MESH — Decentralized Multi-Agent Supply Chain Coordination

**Vertex Swarm Challenge 2026 · Track 3: Agent Economy**

[![Website](https://img.shields.io/badge/agentmesh.world-live-00C48C?style=for-the-badge&logo=globe)](https://agentmesh.world)
[![Docs](https://img.shields.io/badge/docs-agentmesh.world-blue?style=for-the-badge)](https://docs.agentmesh.world)
[![npm](https://img.shields.io/npm/v/@agentmeshworld/sdk?style=for-the-badge&color=cb3837&logo=npm)](https://www.npmjs.com/package/@agentmeshworld/sdk)

**5 autonomous agent roles · BFT consensus · LLM-powered decisions · Self-healing · Enterprise SaaS**

[Live Demo](https://agentmesh.world) · [API Docs](https://docs.agentmesh.world) · [TypeScript SDK](https://www.npmjs.com/package/@agentmeshworld/sdk) · [Dashboard](https://agentmesh.world/dashboard)

</div>

---

MESH is a fully decentralized multi-agent system where autonomous agents negotiate, trade, ship, inspect, and settle supply chain orders — all without a central orchestrator. Agents coordinate exclusively through BFT-ordered MQTT messages on **Tashi Vertex / FoxMQ**, achieving consensus via Hashgraph gossip with sub-100ms latency.

Every agent makes intelligent decisions powered by **LLM providers** (Amazon Bedrock + OpenRouter) with automatic fallback to deterministic heuristics. The system ships as a **production-grade SaaS platform** with multi-tenant workspaces, six granular RBAC roles, agent performance analytics, custom scenario builder, SLA monitoring, webhook integrations, an agent marketplace, dual payment providers, a TypeScript SDK, and a real-time dashboard.

```
                         FoxMQ BFT Cluster (4 nodes)
                        +-----------+-----------+
                        |  Hashgraph Consensus  |
                        +-----------+-----------+
                              |  MQTT 5.0
             +----------------+----------------+
             |        |        |        |      |
          Buyer   Supplier  Logistics Inspector Oracle
                   (x2)         ↑ LLM-powered decisions
                                |
    ┌───────────────────────────┴───────────────────────────┐
    │              MESH SaaS Platform (FastAPI)              │
    │  Auth · RBAC · Analytics · Scenarios · SLA · Webhooks │
    │  Marketplace · Billing · API Keys · Event Sink        │
    └───────────────────────────────────────────────────────┘
                                |
              ┌─────────────────┼─────────────────┐
              │                 │                  │
         Dashboard        TypeScript SDK       REST API
        (SvelteKit)    @agentmeshworld/sdk    /api/v1/*
```

## Why MESH Wins

| Criterion | MESH |
|-----------|------|
| Multi-agent coordination | 5 distinct roles, pure P2P via BFT-ordered MQTT — zero central orchestration |
| Swarm intelligence | LLM-powered decisions (Bedrock + OpenRouter) with circuit-breaker fallback to heuristics |
| Economic model | MESH_CREDIT currency, escrow, settlement splits, 3% deflationary burn |
| Resilience | Heartbeat failure detection, quorum confirmation, role redistribution, LLM-optimized recovery |
| Enterprise SaaS | Multi-tenant workspaces, 6-role RBAC, analytics, SLA monitoring, webhooks, agent marketplace |
| Developer experience | Published TypeScript SDK + CLI, OpenAPI spec, AsyncAPI spec, Fern-generated docs |
| Vertex integration | 4-node FoxMQ cluster, BFT ordering guarantees deterministic state convergence |
| Testing | 292+ tests (unit + integration + chaos + platform + property-based) — all passing |
| Live demo | 3-minute scenario with supplier crash + self-healing recovery |


## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     Dashboard (SvelteKit)                        │
│  AgentCard · OrderFlow · MetricsPanel · EventLog · ChaosControls│
├─────────────────────────────────────────────────────────────────┤
│                  WebSocket Gateway + Bridge                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐           │
│  │  Buyer   │ │ Supplier │ │ Logistics│ │ Inspector│  + Oracle  │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘           │
│  ┌──────────────────────────────────────────────────┐           │
│  │              BaseAgent ABC                        │           │
│  │  Identity · State · Registry · Ledger · Reputation│           │
│  ├──────────────────────────────────────────────────┤           │
│  │  LLM Router (Bedrock ↔ OpenRouter, circuit breaker)│          │
│  └──────────────────────────────────────────────────┘           │
│  ┌──────────────────────────────────────────────────┐           │
│  │  Negotiation Engine · Self-Healing · Arbiter      │           │
│  └──────────────────────────────────────────────────┘           │
│                                                                  │
├─────────────────────────────────────────────────────────────────┤
│              FoxMQ BFT MQTT Cluster (4 nodes)                    │
│              Hashgraph Gossip · MQTT 5.0 · Sub-100ms             │
├─────────────────────────────────────────────────────────────────┤
│                   SaaS Platform (FastAPI)                         │
│  Auth · RBAC (6 roles) · Analytics · Scenarios · SLA Monitoring  │
│  Webhooks · Agent Marketplace · Payments · Event Sink            │
│  PostgreSQL · Xendit · Cryptomus · Tenant Isolation               │
└─────────────────────────────────────────────────────────────────┘
```

### Agent Roles

| Role | Responsibilities | LLM-Powered |
|------|-----------------|-------------|
| **Buyer** | Publishes purchase orders, evaluates bids, negotiates prices, locks escrow | Bid evaluation, settlement calculation |
| **Supplier** | Bids on orders, fulfills committed orders, manages inventory and costs | Pricing strategy, counter-offer negotiation |
| **Logistics** | Bids on shipping requests, handles pickup/transit/delivery lifecycle | Shipping quote calculation (weight, fragility, urgency) |
| **Inspector** | Performs quality inspection, issues pass/partial/reject reports | Category-specific quality assessment |
| **Oracle** | Publishes market prices and demand forecasts each epoch | Price determination, demand forecasting |

### Protocol Phases

```
DISCOVER → REQUEST → BID → NEGOTIATE → COMMIT → EXECUTE → VERIFY → SETTLE
    |          |        |        |          |         |         |         |
 announce   publish  collect  counter    escrow    ship +    inspect   release
 + heartbeat order    bids   (max 3)     lock     fulfill   quality   escrow
```

### Key Technical Decisions

- **No central orchestrator** — all coordination through FoxMQ-ordered MQTT topics
- **Deterministic state** — same BFT-ordered messages = identical state on every agent
- **Ed25519 identity** — each agent has a cryptographic keypair; `agent_id = SHA-256(pubkey)[:16]`
- **HMAC-SHA256 signing** — all message envelopes are signed and verified
- **Hybrid Logical Clocks** — causal ordering across topics, even with clock skew
- **Per-capability reputation** — score per skill (not global), decay toward neutral (0.5)
- **LLM-first with fallback** — every agent tries LLM for decisions, falls back to deterministic heuristics
- **Multi-tenant isolation** — tenant-prefixed MQTT topics (`mesh/{slug}/orders/...`)


## LLM-Powered Agent Intelligence

Every agent in the mesh uses LLM providers for intelligent decision-making, with automatic fallback to deterministic heuristics when LLM calls fail or are disabled.

```
Agent Decision → LLM Router → Primary (Bedrock) → ✓ Use LLM result
                     │                  ↓ fail
                     │         Fallback (OpenRouter) → ✓ Use LLM result
                     │                  ↓ fail
                     └──────→ Deterministic Heuristic → ✓ Always works
```

**11 specialized prompt templates** drive agent decisions:

| Decision | Agent | What the LLM Does |
|----------|-------|--------------------|
| Market pricing | Oracle | Determines fair prices from supply/demand signals and history |
| Demand forecasting | Oracle | Predicts demand trends and supply risk |
| Bid creation | Supplier | Cost-aware pricing with profit margin optimization |
| Bid evaluation | Buyer | Multi-criteria scoring with capability matching |
| Counter-offers | Buyer/Supplier | Adaptive negotiation based on competition and round pressure |
| Quality inspection | Inspector | Category-specific assessment (electronics, textiles, food) |
| Shipping quotes | Logistics | Weight/fragility/urgency-based pricing with capacity pressure |
| Dispute resolution | Arbiter | Evidence-based settlement with precedent tracking |
| Healing analysis | Detector | Failure diagnosis with capability-aware agent replacement |
| Recovery parameters | Recovery | Role-specific recovery epochs and load factors |
| Settlement calculation | Buyer | Quality/timeliness bonuses and penalty computation |

**LLM Router features:**
- Multi-provider support (Amazon Bedrock + OpenRouter)
- Circuit breaker pattern (trips after 5 failures, 60s cooldown)
- Latency tracking and cost estimation per call
- Usage callback for billing integration
- JSON response parsing with validation

### Negotiation Strategies

Four pluggable strategies compute counter-offer prices:

| Strategy | Buyer Behavior | Supplier Behavior |
|----------|---------------|-------------------|
| **Aggressive** | Push 40% toward 90% of market price | Minimal 5% discount |
| **Conservative** | 5-10% below their price, shrinking per round | 3% discount |
| **Adaptive** | 5-15% discount based on competition + round pressure | 2-8% based on competition |
| **LLM** | Dynamic counter-offer via prompt | Context-aware pricing |


## SaaS Platform

MESH ships with a full **enterprise SaaS control plane** built on FastAPI + PostgreSQL, turning the decentralized agent framework into a managed service with comprehensive operational tooling.

### Platform API (`/api/v1`)

| Endpoint Group | Capabilities |
|----------------|-------------|
| **Auth** | Registration, login, JWT access/refresh tokens |
| **Workspaces** | Multi-tenant CRUD, slug-based isolation, role assignment with escalation prevention |
| **RBAC** | 6 granular roles (owner, admin, operator, developer, auditor, viewer) with hierarchical permissions |
| **Analytics** | Per-agent performance metrics, order lifecycle timelines, economic health aggregations |
| **Scenarios** | Custom supply chain scenario builder with validation, built-in system scenarios |
| **SLA Monitoring** | Rule-based threshold monitoring, breach detection, alert management with acknowledgment |
| **Webhooks** | Outbound event notifications with HMAC-SHA256 signing, retry logic, delivery tracking |
| **Marketplace** | Agent template registry, search/filter, instantiation with parameter overrides |
| **Orders** | Order management with event sourcing, status tracking, bid counts |
| **Ledger** | Transaction queries, balance lookups, settlement history |
| **Agents** | Agent management, status monitoring, capability tracking |
| **Payments** | Xendit (fiat: IDR, PHP, THB, VND, MYR) + Cryptomus (crypto: BTC, ETH, USDT, SOL, 150+ tokens) |
| **API Keys** | Key generation with `amk_` prefix, scoped permissions, revocation |
| **Admin** | Platform analytics, usage summaries, quota checks, CSV export, plan management |

### Enhanced RBAC (6 Roles)

| Role | Level | Access Scope |
|------|-------|-------------|
| **Owner** | 6 | Full access, ownership transfer, role assignment |
| **Admin** | 5 | Everything except ownership transfer |
| **Operator** | 4 | Agent management, scenario execution, order operations |
| **Developer** | 3 | API keys, SDK endpoints, integration management |
| **Auditor** | 2 | Analytics, audit logs, webhook delivery history (read-only) |
| **Viewer** | 1 | Read-only access to workspace data |

Role assignment includes escalation prevention — users cannot assign roles at or above their own level.

### Agent Performance Analytics

Three analytics endpoints aggregate data from existing event-sourced tables:

- **Agent Metrics** — per-agent order counts, success rates, average settlement times, reputation scores
- **Order Timeline** — phase transition durations for each order through the protocol lifecycle
- **Economic Health** — total ledger volume, average transaction size, escrow utilization, burn amounts

All accept a configurable time range (1-365 days) and return zero-valued metrics when no data exists.

### Custom Scenario Builder

Define and manage supply chain simulations with configurable:
- Agent role configurations (role, count, initial balance, capabilities)
- Goods catalogs (name, category, base price, volatility)
- Order timelines (scheduled order placement)
- Chaos events (agent kills, network partitions)

Validation enforces at least one buyer, one supplier, and one goods definition. Built-in system scenarios are auto-discovered from the framework.

### SLA Monitoring & Alerts

Define performance thresholds and get alerted on breaches:
- **Metric types**: order settlement time, agent uptime, order success rate
- **Operators**: greater_than, less_than (strict comparison)
- **On-demand evaluation** triggers metric computation and creates alerts for breaches
- **Alert management** with acknowledgment tracking (user ID + timestamp)

### Webhook & Integration Layer

- **Outbound webhooks** with HTTPS URL validation and HMAC-SHA256 signed payloads
- **Retry logic** — up to 3 attempts with exponential backoff (10s, 30s, 90s)
- **Delivery tracking** — full history with HTTP status codes and response bodies
- **Inbound triggers** — external systems can create orders via POST

### Agent Marketplace

- **Register** reusable agent templates with role, capabilities, config, and defaults
- **Search** by text query, role filter, or capability filter — ordered by popularity
- **Instantiate** templates into workspaces with parameter overrides
- **Usage tracking** — templates track instantiation count

### Multi-Tenant Architecture

```
SDK Agent → WebSocket Gateway → TenantTransport → mesh/{slug}/orders/...
                                                         ↓
                                              MQTT Event Sink → PostgreSQL
                                                         ↓
                                              Dashboard / REST API
```

- **Workspace isolation** — each workspace gets its own MQTT topic namespace
- **TenantTransport** — automatically prefixes all MQTT topics with the workspace slug
- **Event sink** — subscribes to `mesh/*` and persists events to PostgreSQL with idempotent processing
- **Usage-based billing** — LLM token tracking, cost estimation, credit deduction per workspace

### Payment Providers

| Provider | Type | Currencies | Integration |
|----------|------|-----------|-------------|
| **Xendit** | Fiat | IDR, PHP, THB, VND, MYR | Invoice creation, HMAC-SHA256 webhook verification |
| **Cryptomus** | Crypto | BTC, ETH, USDT, SOL, 150+ tokens | Payment request, webhook verification |


## TypeScript SDK & CLI

Connect your own agents to the mesh network with the published npm package:

```bash
npm install @agentmeshworld/sdk
```

```typescript
import { Agent } from "@agentmeshworld/sdk";

const agent = new Agent({
  url: "wss://agentmesh.world/ws/v1/agent",
  apiKey: "amk_your_api_key_here",
  role: "supplier",
  capabilities: ["electronics", "semiconductors"],
});

await agent.connect();
agent.subscribe(["order:request", "order:bid"]);

agent.on("message", ({ topic, payload }) => {
  if (topic.includes("/request")) {
    agent.publish("order:bid", {
      order_id: payload.order_id,
      supplier_id: agent.agentId,
      price_per_unit: payload.max_price_per_unit * 0.9,
      available_quantity: payload.quantity,
    });
  }
});
```

**CLI for quick testing:**

```bash
npx @agentmeshworld/sdk connect --key amk_your_key --role buyer --sub order:bid,order:status
```

The SDK provides:
- Type-safe interfaces for all 22 MESH protocol message types
- WebSocket transport with auto-reconnect and exponential backoff
- Friendly event-to-topic mapping (`order:request` → `orders/+/request`)
- Interactive CLI mode for live message inspection and publishing


## Economic Model

Currency: **MESH_CREDIT** (fiat-like, initialized per agent)

### Settlement Distribution

| Recipient | Share | Purpose |
|-----------|-------|---------|
| Supplier | 92% | Goods payment |
| Logistics | 3% | Shipping fee |
| Inspector | 2% | Quality inspection fee |
| Burned | 3% | Deflationary mechanism |

### Dispute Resolution

The deterministic Arbiter resolves disputes based on inspection reports (with optional LLM-powered analysis):

- **Quality ≥ threshold** — accepted, no penalties
- **Quality ≥ 80% of threshold** — partial refund proportional to defects, -0.08 reputation
- **Quality < 80% of threshold** — full refund, -0.15 reputation slash
- **Late delivery** — 2-10% penalty depending on lateness ratio
- **No-show** — -0.15 reputation slash (byzantine-level)

### Reputation Engine

Per-capability scoring (not global reputation). Each agent has a score per skill:

| Event | Score Delta |
|-------|-------------|
| Successful fulfillment | +0.05 |
| On-time delivery | +0.03 |
| High quality (> 0.9) | +0.02 |
| Late delivery | -0.04 |
| Quality failure | -0.08 |
| No-show | -0.15 |
| Byzantine behavior | -0.25 |
| Epoch decay | → 0.5 (factor 0.98) |

Bid scoring weights: **price 35%** · **reputation 30%** · **speed 20%** · **confidence 15%**


## Self-Healing

```
Heartbeat miss → SUSPECT (3 missed) → DEAD (6 missed)
                                            |
                                  Quorum vote (≥ 2 agents)
                                            |
                                  Role redistribution
                                            |
                                  Agent recovers → REJOINING (50% load, 2 epochs)
                                            |
                                         ACTIVE
```

- **Detection** — each agent runs a `FailureDetector` monitoring peer heartbeats
- **Confirmation** — death requires quorum (≥ 2 independent detectors agree)
- **Redistribution** — longest-uptime active peer becomes coordinator, reassigns orders to capability-matched agents
- **Recovery** — rejoining agents operate at 50% capacity for 2 epochs; LLM optimizes recovery parameters per role
- **Degraded mode** — if no suitable replacement exists, the system continues in degraded mode rather than failing


## Real-Time Dashboard

The SvelteKit dashboard provides live visualization of the entire mesh network:

| Component | Shows |
|-----------|-------|
| **AgentCard** | Per-agent status, role, capabilities, load, state |
| **OrderFlow** | Order pipeline progression through all 8 protocol phases |
| **MetricsPanel** | Ledger balances, transaction counts, reputation scores |
| **EventLog** | Scrolling log of all MQTT messages with timestamps |
| **ChaosControls** | Buttons to trigger agent kills/restarts during demo |

Additional features: guided tour (driver.js), demo engine with mock data, D3 force-directed topology graphs, multi-workspace switching, auth flow.


## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+ (for dashboard and SDK)
- Docker & Docker Compose (for full deployment)

### Install

```bash
# Python agent framework
cd mesh && pip install -e ".[dev]"

# Dashboard
cd dashboard && npm install

# TypeScript SDK (for building custom agents)
npm install @agentmeshworld/sdk
```

### Run Tests

```bash
# Agent framework tests (152 tests)
make test-unit     # 100 unit tests — core + negotiation + reputation
make test-int      # 31 integration tests — discovery, order lifecycle, settlement
make test-chaos    # 21 chaos tests — self-healing, failure recovery

# Platform tests (140 tests, including property-based)
cd mesh && python -m pytest ../platform_tests/ -v

# All agent tests at once
python -m pytest tests/ -v
```

### Full Deployment (Docker)

```bash
# Core stack: 4-node FoxMQ cluster + 6 agents + bridge + dashboard
docker compose up --build

# Full SaaS stack: + PostgreSQL + Platform API + Event Sink
docker compose -f docker-compose.yml -f docker-compose.saas.yml up --build
```

| Service | URL |
|---------|-----|
| Dashboard | http://localhost:3000 |
| WebSocket Bridge | ws://localhost:8080 |
| Platform API | http://localhost:8000 |
| API Docs | http://localhost:8000/docs |

### Run Demo Scenario

```bash
make demo
```

The "Laptop Supply Chain" scenario runs for 3 minutes:
1. **t=8s** — Buyer orders 50 laptop displays (max $120/unit)
2. **t=50s** — Buyer orders 100 laptop batteries (max $50/unit)
3. **t=70s** — Supplier A crashes — failure detected, roles redistributed
4. **t=100s** — Buyer orders 75 keyboards (max $30/unit)
5. **t=110s** — Supplier A recovers — rejoins at 50% capacity for 2 epochs

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


## API Documentation

Full API documentation is generated with [Fern](https://buildwithfern.com) and published at **[docs.agentmesh.world](https://docs.agentmesh.world)**.

Includes:
- **OpenAPI 3.0 spec** — all REST API endpoints with schemas
- **AsyncAPI 3.0 specs** — MQTT protocol topics and WebSocket gateway protocol
- **Tutorials** — Build a Buyer Agent, Build a Supplier Agent, Full Supply Chain, IoT Inspector
- **SDK Reference** — TypeScript SDK API, CLI commands, code examples
- **Architecture docs** — System overview, agent roles, economic model, security, self-healing

```bash
pnpm fern:check     # Validate API spec
pnpm fern:publish   # Publish docs
```


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
| JWT + bcrypt auth | Platform API access |
| 6-role RBAC with escalation prevention | Privilege escalation |
| Scoped API keys | SDK/CLI access control |
| Tenant-prefixed MQTT topics | Cross-workspace data leakage |
| Webhook HMAC-SHA256 signatures | Webhook spoofing |
| HTTPS-only webhook URLs | Man-in-the-middle attacks |


## Project Structure

```
Project-Vertex/
├── mesh/                        Python agent framework (installable package)
│   ├── core/                    Identity, crypto, clock, config, messages, protocol,
│   │                            topics, state, registry, ledger, reputation, transport
│   ├── agents/                  BaseAgent ABC + 5 role implementations
│   ├── negotiation/             Multi-round engine, 4 strategies, dispute arbiter
│   ├── healing/                 Failure detection, role redistribution, recovery
│   ├── llm/                     LLM router, Bedrock + OpenRouter providers, 11 prompts
│   ├── scenarios/               Demo scenarios
│   └── cli.py                   CLI entry point
├── mesh_platform/               SaaS platform (FastAPI + PostgreSQL)
│   ├── routers/                 14 API route groups
│   │   ├── auth.py              Registration, login, JWT
│   │   ├── workspaces.py        Workspace CRUD + role assignment
│   │   ├── analytics.py         Agent metrics, order timeline, economic health
│   │   ├── scenarios.py         Custom scenario builder CRUD
│   │   ├── sla.py               SLA rules, evaluation, alerts
│   │   ├── webhooks.py          Webhook registration, delivery, inbound triggers
│   │   ├── marketplace.py       Agent template registry + instantiation
│   │   ├── orders.py            Order management
│   │   ├── ledger.py            Ledger queries
│   │   ├── agents.py            Agent management
│   │   ├── payments.py          Xendit + Cryptomus billing
│   │   ├── api_keys.py          API key management
│   │   ├── capabilities.py      Capability catalog
│   │   └── admin.py             Admin endpoints
│   ├── models/                  17 SQLAlchemy ORM models
│   ├── schemas/                 Pydantic request/response schemas
│   ├── services/                Business logic layer (8 services)
│   ├── gateway/                 WebSocket gateway
│   ├── sink/                    MQTT event subscriber → PostgreSQL
│   └── payments/                Payment provider integrations
├── bridge/                      MQTT → WebSocket bridge for dashboard
├── dashboard/                   SvelteKit real-time UI
├── packages/sdk/                @agentmeshworld/sdk — TypeScript SDK + CLI
├── fern/                        API docs (OpenAPI, AsyncAPI, tutorials)
├── tests/                       152 agent framework tests
├── platform_tests/              140 platform tests (unit + property-based)
├── docker-compose.yml           Core stack
├── docker-compose.saas.yml      SaaS overlay
└── Makefile                     Build/test/deploy commands
```


## Testing

| Suite | Count | Focus |
|-------|-------|-------|
| Unit | 100 | Core components (crypto, identity, ledger, messages, negotiation, reputation, state) |
| Integration | 31 | Cross-component workflows (discovery, order lifecycle, settlement) |
| Chaos | 21 | Failure injection, recovery, redistribution |
| Platform Unit | 87 | Auth, workspaces, payments, API keys, gateway, event sink, scenarios, marketplace, SLA |
| Platform PBT | 53 | Property-based tests (Hypothesis) — 11 correctness properties, 100+ iterations each |
| **Total** | **292+** | **All passing** |

### Correctness Properties (Property-Based Testing)

All platform features are validated with formal correctness properties using Hypothesis:

| # | Property | What It Validates |
|---|----------|-------------------|
| 1 | Analytics aggregation correctness | Per-agent order counts, ledger volume, avg transaction size |
| 2 | Order lifecycle duration computation | Phase transition durations sum to total order time |
| 3 | Webhook HTTPS URL validation | Only `https://` URLs accepted |
| 4 | Scenario serialization round-trip | JSON serialize → deserialize produces equal objects |
| 5 | Scenario validation rejects invalid | Missing buyer/supplier/goods, invalid prices rejected |
| 6 | SLA breach detection correctness | Breach iff (gt AND actual > threshold) OR (lt AND actual < threshold) |
| 7 | RBAC permission check | Role-in-permitted-set for all 4 permission levels |
| 8 | Role escalation prevention | Self-assignment to higher role always rejected |
| 9 | Marketplace search filtering/ordering | Results match filters, ordered by usage count DESC |
| 10 | Template instantiation merge | Overrides applied, defaults preserved for non-overridden fields |
| 11 | Template name validation | Accepted iff 3-100 chars, duplicates rejected |


## Configuration

### Agent Configuration (prefix `MESH_`)

| Variable | Default | Description |
|----------|---------|-------------|
| `MESH_BROKER_HOST` | `127.0.0.1` | FoxMQ broker hostname |
| `MESH_BROKER_PORT` | `1883` | MQTT port |
| `MESH_AGENT_ROLE` | `buyer` | Agent role |
| `MESH_CAPABILITIES` | `` | Comma-separated capabilities |
| `MESH_INITIAL_BALANCE` | `10000` | Starting MESH_CREDIT balance |
| `MESH_HEARTBEAT_INTERVAL` | `5.0` | Seconds between heartbeats |
| `MESH_NEGOTIATE_MAX_ROUNDS` | `3` | Max counter-offer rounds |
| `MESH_LLM_ENABLED` | `true` | Enable/disable LLM for agent decisions |
| `MESH_LLM_PRIMARY_PROVIDER` | `bedrock` | Primary LLM provider |
| `MESH_LLM_FALLBACK_PROVIDER` | `openrouter` | Fallback LLM provider |

### Platform Configuration (prefix `PLATFORM_`)

| Variable | Default | Description |
|----------|---------|-------------|
| `PLATFORM_DATABASE_URL` | `postgresql+asyncpg://...` | PostgreSQL connection string |
| `PLATFORM_SECRET_KEY` | — | JWT signing secret |
| `PLATFORM_MQTT_HOST` | `127.0.0.1` | MQTT broker for event sink |
| `PLATFORM_XENDIT_SECRET_KEY` | — | Xendit payment provider key |
| `PLATFORM_CRYPTOMUS_MERCHANT_ID` | — | Cryptomus merchant ID |
| `PLATFORM_CRYPTOMUS_API_KEY` | — | Cryptomus API key |

See `.env.example` for the full list.


## Team

**Hitazurana (HiroJei)** · [Tomeku Development](https://tomeku.com) — Vertex Swarm Challenge 2026

## License

MIT
