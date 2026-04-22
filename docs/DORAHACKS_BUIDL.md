# DoraHacks BUIDL Submission — MESH

Use this document to fill in the DoraHacks BUIDL submission form for the Vertex Swarm Challenge 2026, Track 3: Agent Economy.

---

## BUIDL Name

```
MESH — Decentralized Multi-Agent Supply Chain Coordination
```

## Track

```
🧠 Track 3 | Agent Economy (AI Agentic Coordination Layer)
```

## One-Line Description (Tagline)

```
5 autonomous AI agents negotiate, trade, and settle supply chain orders over BFT-ordered FoxMQ — zero orchestrator, LLM-powered decisions, self-healing, enterprise SaaS.
```

## Short Description (~200 words)

```
MESH is a fully decentralized multi-agent supply chain coordination system built for the Vertex Swarm Challenge 2026 (Track 3: Agent Economy). Five autonomous agent roles — Buyer, Supplier, Logistics, Inspector, and Oracle — discover each other, negotiate prices, commit to orders, execute fulfillment, verify quality, and settle payments, all without a central orchestrator.

Agents coordinate exclusively through BFT-ordered MQTT messages on a 4-node FoxMQ Hashgraph cluster, achieving deterministic state convergence with sub-100ms latency. Every agent makes intelligent decisions powered by LLM providers (Amazon Bedrock + OpenRouter) with automatic fallback to deterministic heuristics.

The economic model uses MESH_CREDIT currency with a double-entry ledger, escrow-based settlement, per-capability reputation scoring, and a 3% deflationary burn. When agents fail, the system self-heals: heartbeat detection, quorum-confirmed death, automatic role redistribution, and graceful recovery.

MESH ships as a production-grade enterprise SaaS platform with multi-tenant workspaces, 6-role RBAC, agent analytics, custom scenario builder, SLA monitoring, webhook integrations, an agent marketplace, dual payment providers (fiat + crypto), a published TypeScript SDK on npm, and a real-time SvelteKit dashboard. 292+ tests passing, including 11 formal correctness properties validated with property-based testing.
```

## Long Description / README (Markdown)

```
Paste the full content of README.md here, or link to the GitHub repo.
```

## Links

| Field | Value |
|-------|-------|
| **GitHub Repository** | `https://github.com/Tomeku-Development/AgentMesh` |
| **Live Demo** | `https://agentmesh.world` |
| **API Documentation** | `https://docs.agentmesh.world` |
| **Dashboard** | `https://agentmesh.world/dashboard` |
| **TypeScript SDK (npm)** | `https://www.npmjs.com/package/@agentmeshworld/sdk` |
| **Demo Video** | *(add your video URL here)* |

## Tech Stack

```
Python 3.11, FastAPI, SQLAlchemy 2.0, PostgreSQL, FoxMQ (Hashgraph BFT), MQTT 5.0, SvelteKit, TypeScript, D3.js, Amazon Bedrock, OpenRouter, Xendit, Cryptomus, Docker, Hypothesis (PBT)
```

## Team

| Name | Role |
|------|------|
| **Hitazurana (HiroJei)** | Solo builder — [Tomeku Development](https://tomeku.com) |

---

## Track 3 Judging Criteria Responses

The Track 3 judging criteria are: Coordination Correctness, Resilience, Auditability, Security Posture, and Developer Clarity. Below is how MESH addresses each one.

---

### 1. Coordination Correctness

> "No double assignments, deterministic resolution under contention."

**How MESH delivers this:**

- **BFT-ordered message sequencing**: All agent messages flow through a 4-node FoxMQ Hashgraph cluster. Every node sees the same total order of messages, guaranteeing identical state on every agent. Two suppliers bidding on the same order will always resolve deterministically — the first bid in BFT order wins the commit.

- **8-phase protocol with escrow**: Orders progress through DISCOVER → REQUEST → BID → NEGOTIATE → COMMIT → EXECUTE → VERIFY → SETTLE. Escrow locks funds at COMMIT, preventing double-spend. Settlement only releases after Inspector verification.

- **No double assignments**: The Buyer agent evaluates bids using a weighted scoring function (price 35%, reputation 30%, speed 20%, confidence 15%) and commits to exactly one supplier per order. The BFT ordering ensures all agents agree on which bid was selected.

- **Deterministic dispute resolution**: The Arbiter uses quality inspection reports to compute settlements. Same inputs always produce the same outcome — partial refunds, reputation penalties, and escrow releases are all deterministic.

- **Formally verified with property-based testing**: 11 correctness properties validated with Hypothesis (100+ iterations each). Properties cover analytics aggregation, SLA breach detection, RBAC permissions, scenario validation, and marketplace operations.

---

### 2. Resilience

> "The swarm continues to operate gracefully when nodes drop or messages are delayed."

**How MESH delivers this:**

- **Self-healing pipeline**: Heartbeat monitoring → SUSPECT (3 missed) → DEAD (6 missed) → Quorum vote (≥2 agents confirm) → Role redistribution → Recovery (50% capacity for 2 epochs) → Full ACTIVE.

- **Live demo proves it**: At t=70s in the demo scenario, Supplier A crashes. The system detects the failure, confirms death via quorum, redistributes Supplier A's orders to Supplier B, and continues processing new orders without interruption. At t=110s, Supplier A recovers and rejoins at 50% capacity.

- **LLM fallback chain**: Every agent decision tries Primary LLM (Bedrock) → Fallback LLM (OpenRouter) → Deterministic heuristic. Circuit breaker trips after 5 failures with 60s cooldown. Agents never stop making decisions.

- **Degraded mode**: If no capability-matched replacement exists for a failed agent, the system continues in degraded mode rather than halting.

- **21 chaos tests**: Dedicated test suite for failure injection, recovery verification, and redistribution correctness.

---

### 3. Auditability

> "A clear, complete, and verifiable Proof of Coordination. The goal is auditability, not blockchain theater."

**How MESH delivers this:**

- **Event-sourced audit trail**: Every state transition is an `OrderEvent` persisted to PostgreSQL via the MQTT Event Sink. The full history of who did what and when is queryable via the REST API.

- **Cryptographic message integrity**: Every message envelope is signed with HMAC-SHA256. The agent's Ed25519 identity (`agent_id = SHA-256(pubkey)[:16]`) is embedded in every message. Replay detection via nonce cache with 60-second freshness window.

- **Double-entry ledger**: Every MESH_CREDIT transfer is recorded as a `LedgerEntry` with from_agent, to_agent, amount, tx_type, and timestamp. The ledger always balances (minus the 3% burn).

- **Per-order timeline**: The Analytics API returns the exact duration between every phase transition for every order — a complete Proof of Coordination showing the negotiate → commit → execute → verify → settle loop with timestamps.

- **Webhook delivery log**: Every outbound webhook delivery is tracked with HTTP status codes, response bodies, attempt numbers, and timestamps.

---

### 4. Security Posture

> "Evidence of message integrity and resistance to replay attacks."

**How MESH delivers this:**

| Mechanism | Threat Mitigated |
|-----------|-----------------|
| Ed25519 keypairs | Agent impersonation — each agent has a unique cryptographic identity |
| HMAC-SHA256 envelope signing | Message tampering — all envelopes are signed and verified |
| Nonce cache + replay detector | Replay attacks — duplicate message IDs are rejected |
| 60-second freshness window | Stale message injection — old messages are discarded |
| BFT consensus (4-node FoxMQ) | Byzantine broker nodes — Hashgraph tolerates f < n/3 failures |
| Escrow mechanism | Payment fraud — funds locked until Inspector verification |
| Per-capability reputation | Sybil attacks — reputation is costly to build, per-skill |
| Quorum-based failure detection | False positive kills — death requires ≥2 independent confirmations |
| JWT + bcrypt auth | Platform API access control |
| 6-role RBAC with escalation prevention | Privilege escalation — users cannot assign roles above their own |
| HTTPS-only webhook URLs | Man-in-the-middle on webhook delivery |
| Webhook HMAC-SHA256 signatures | Webhook spoofing — receivers can verify payload authenticity |
| Tenant-prefixed MQTT topics | Cross-workspace data leakage |

---

### 5. Developer Clarity

> "Runnable repo, clear demo flow, observability."

**How MESH delivers this:**

- **One-command deployment**: `docker compose -f docker-compose.yml -f docker-compose.saas.yml up --build` launches the full stack — 4-node FoxMQ cluster, 6 agents, bridge, dashboard, PostgreSQL, Platform API, and Event Sink.

- **`make demo`**: Runs a 3-minute "Laptop Supply Chain" scenario with scheduled orders, a supplier crash at t=70s, self-healing recovery, and full settlement.

- **Real-time dashboard**: SvelteKit UI with agent cards, order flow visualization, metrics panels, event log, and chaos controls — all updating live via WebSocket.

- **Published TypeScript SDK**: `npm install @agentmeshworld/sdk` — type-safe interfaces for all 22 protocol message types, WebSocket transport with auto-reconnect, CLI for quick testing.

- **API documentation**: Fern-generated docs at docs.agentmesh.world with OpenAPI 3.0 spec, AsyncAPI 3.0 specs, tutorials, and SDK reference.

- **292+ tests**: Unit (100) + Integration (31) + Chaos (21) + Platform (140, including 53 property-based tests). All passing. Tests run without a live broker — fully self-contained.

- **Clean project structure**: 14 API routers, 17 ORM models, 8 service modules, clear separation of concerns (routers → services → models).

---

## Tashi Integration Pillars

### FoxMQ (Vertex under the hood)

- 4-node FoxMQ Hashgraph cluster for BFT consensus
- MQTT 5.0 transport with QoS mapping per message type
- Tenant-prefixed topics (`mesh/{slug}/orders/...`) for multi-workspace isolation
- Event Sink subscribes to `mesh/*` and persists all events to PostgreSQL with idempotent processing

### Agent Implementation

- Python agents using `paho-mqtt` connecting to FoxMQ nodes
- 5 distinct agent roles with specialized decision logic
- LLM-powered decisions via Amazon Bedrock + OpenRouter
- Ed25519 identity with HMAC-SHA256 message signing

---

## Demo Flow (3 minutes)

| Time | What Happens |
|------|-------------|
| 0:00 | 6 agents boot, discover each other via heartbeats, Oracle publishes market prices |
| 0:08 | Buyer orders 50 laptop displays (max $120/unit) — full negotiate → commit → execute → verify → settle cycle |
| 0:50 | Buyer orders 100 laptop batteries (max $50/unit) |
| 1:10 | **Supplier A crashes** — heartbeat failure detected, quorum confirms death, orders redistributed to Supplier B |
| 1:40 | Buyer orders 75 keyboards (max $30/unit) — processed by remaining agents |
| 1:50 | **Supplier A recovers** — rejoins at 50% capacity for 2 epochs, then full capacity |
| 3:00 | Scenario complete — all orders settled, ledger balanced, reputation updated |

**What to observe in the dashboard:**
- Agent cards showing status transitions (ACTIVE → SUSPECT → DEAD → REJOINING → ACTIVE)
- Order flow pipeline progressing through all 8 phases
- Ledger balances updating in real-time
- Event log showing every MQTT message with timestamps

---

## Key Metrics

| Metric | Value |
|--------|-------|
| Agent roles | 5 (Buyer, Supplier, Logistics, Inspector, Oracle) |
| Protocol phases | 8 (DISCOVER → SETTLE) |
| FoxMQ nodes | 4 (Hashgraph BFT cluster) |
| LLM prompt templates | 11 specialized decision templates |
| RBAC roles | 6 (owner → viewer) |
| API endpoints | 50+ across 14 router groups |
| ORM models | 17 SQLAlchemy models |
| Tests | 292+ (unit + integration + chaos + platform + PBT) |
| Correctness properties | 11 (validated with Hypothesis, 100+ iterations each) |
| Payment providers | 2 (Xendit fiat + Cryptomus crypto) |
| SDK | Published on npm (@agentmeshworld/sdk) |

---

## Submission Checklist

- [ ] BUIDL created on DoraHacks with project name and description
- [ ] Track selected: Track 3 | Agent Economy
- [ ] GitHub repository linked: `https://github.com/Tomeku-Development/AgentMesh`
- [ ] Live demo URL added: `https://agentmesh.world`
- [ ] Demo video uploaded/linked
- [ ] Team members listed
- [ ] All links verified (docs, npm, dashboard)
- [ ] Pinged in Discord #shipping-log channel
