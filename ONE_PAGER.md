# MESH
## The TCP/IP for Supply Chain Swarms

**Vertex Swarm Challenge 2026 | Track 3: The Agent Economy**

---

### The Problem

Centralized orchestrators are single points of failure. Multi-vendor robots can't coordinate without proprietary middleware. When nodes fail, systems crash. Economic coordination requires trust without central authorities.

### The Solution

**MESH** is a fully decentralized multi-agent supply chain coordination system. No central orchestrator. No single point of failure. Just autonomous agents negotiating, trading, shipping, inspecting, and settling orders at machine speed.

---

### Key Innovations

| Feature | Implementation |
|---------|---------------|
| **Pure P2P Coordination** | BFT-ordered MQTT on 4-node FoxMQ cluster with Hashgraph consensus |
| **5 Agent Roles** | Buyer, Supplier, Logistics, Inspector, Oracle - all autonomous |
| **Self-Healing Swarm** | Quorum-based failure detection + automatic role redistribution |
| **Built-in Economy** | Escrow, settlement (92/3/2/3 split), per-capability reputation, 3% burn |
| **Cryptographic Security** | Ed25519 identity, HMAC-SHA256 signing, Hybrid Logical Clocks |

---

### The Agent Economy Protocol

```
DISCOVER → REQUEST → BID → NEGOTIATE → COMMIT → EXECUTE → VERIFY → SETTLE
```

1. **Discovery**: Agents auto-discover via retained MQTT announcements
2. **Negotiation**: Multi-round bidding with 3 strategies (Aggressive/Conservative/Adaptive)
3. **Settlement**: Deterministic escrow release with reputation updates
4. **Self-Healing**: 30s failure detection, quorum confirmation, 50% capacity recovery ramp-up

---

### Demo: Laptop Supply Chain Crisis (3 Minutes)

| Time | Event |
|------|-------|
| t=8s | Buyer orders 50 displays - suppliers bid and negotiate |
| t=50s | Buyer orders 100 batteries - Supplier B wins |
| **t=70s** | **CHAOS: Supplier A crashes** |
| t=75s | Quorum reached, roles redistributed to Supplier B |
| t=100s | Buyer orders 75 keyboards - continues uninterrupted |
| **t=110s** | **RECOVERY: Supplier A rejoins at 50% capacity** |
| t=130s | Full capacity restored |

**Result:** 3 orders completed, 1 crash recovered, zero human intervention.

---

### Performance Metrics

| Metric | Value |
|--------|-------|
| Test Coverage | **152 tests** (100 unit + 31 integration + 21 chaos) |
| Operation Latency | **Sub-millisecond** (agent-local) |
| Consensus Latency | **~50-100ms** (FoxMQ Hashgraph) |
| Throughput | **103K+ envelopes/sec** |
| Self-Healing Time | **~30s** detection + redistribution |
| Codebase | **~2,500 lines** production Python + Svelte |

---

### Why Track 3: The Agent Economy

| Criteria | MESH |
|----------|------|
| **Leaderless** | No master orchestrator - pure P2P negotiation |
| **Economic** | Full incentive-compatible mechanism design |
| **Autonomous** | Agents decide at machine speed (sub-ms) |
| **Resilient** | Byzantine fault tolerance + self-healing |

---

### Technical Stack

- **Consensus**: Tashi Vertex / FoxMQ (4-node BFT cluster)
- **Transport**: MQTT 5.0 with total ordering guarantees
- **Identity**: Ed25519 keypairs, SHA-256 derived agent IDs
- **Clocks**: Hybrid Logical Clocks for causal consistency
- **Frontend**: SvelteKit real-time dashboard
- **SDK**: TypeScript + Python frameworks

---

### Real-World Applications

- **Warehouse Automation**: Multi-vendor AMRs coordinating without central WMS
- **Drone Delivery**: Multi-operator fleets negotiating airspace
- **Disaster Response**: Search & rescue with degraded connectivity
- **Cross-Company Procurement**: Supply chains without shared infrastructure

---

### Run It Yourself

```bash
git clone [repository]
cd Project-Vertex
docker compose up --build
# Dashboard: http://localhost:3000
```

---

### Team

**Hitazurana** | Vertex Swarm Challenge 2026

Built on Tashi Vertex / FoxMQ | Open Source (MIT)

---

### Key Numbers

| | |
|---|---|
| Agent Roles | 5 (buyer, supplier, logistics, inspector, oracle) |
| Protocol Phases | 8 (discover to settle) |
| Message Types | 22 Pydantic models |
| MQTT Topics | 40+ |
| Negotiation Strategies | 3 |
| Settlement Split | 92% supplier / 3% logistics / 2% inspector / 3% burn |

---

**MESH: The coordination layer for the agent economy.**
