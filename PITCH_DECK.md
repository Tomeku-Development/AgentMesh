# MESH Pitch Deck
## Vertex Swarm Challenge 2026 - Track 3: The Agent Economy

---

## Slide 1: Title

# MESH
### The TCP/IP for Supply Chain Swarms

**Track 3 | The Agent Economy**

Team: Hitazurana

---

## Slide 2: The Problem

### Centralized Coordination is Broken

| Problem | Impact |
|---------|--------|
| **Single Point of Failure** | One orchestrator crash = entire fleet down |
| **Vendor Lock-in** | Multi-vendor robots can't coordinate without proprietary middleware |
| **No Self-Healing** | Failed nodes require manual intervention |
| **Trust Issues** | Economic coordination needs central authorities |

> "The future of autonomy is peer-to-peer. But today's systems still rely on cloud orchestrators."

---

## Slide 3: The Solution

# MESH

### Fully Decentralized Multi-Agent Supply Chain Coordination

| Feature | Implementation |
|---------|---------------|
| **No Central Orchestrator** | Pure P2P via BFT-ordered MQTT on FoxMQ |
| **5 Agent Roles** | Buyer, Supplier, Logistics, Inspector, Oracle |
| **Self-Healing Swarm** | Automatic failure detection & role redistribution |
| **Built-in Economy** | Escrow, settlement, reputation, deflationary burn |

```
DISCOVER --> REQUEST --> BID --> NEGOTIATE --> COMMIT --> EXECUTE --> VERIFY --> SETTLE
```

---

## Slide 4: Technical Architecture

### Built on Tashi Vertex / FoxMQ

```
+-----------------------------------------------------------+
|                    Dashboard (SvelteKit)                   |
+-----------------------------------------------------------+
|                WebSocket Bridge (Python)                   |
+-----------------------------------------------------------+
|  +----------+  +----------+  +----------+  +----------+  |
|  |  Buyer   |  | Supplier |  | Logistics|  | Inspector|  |
|  +----------+  +----------+  +----------+  +----------+  |
|  |  Identity | State | Registry | Ledger | Reputation  |  |
|  +----------------------------------------------------+  |
|  |  Negotiation Engine  |  Self-Healing  |  Arbiter    |  |
|  +----------------------------------------------------+  |
+-----------------------------------------------------------+
|               FoxMQ BFT Cluster (4 nodes)                 |
|               Hashgraph Gossip | MQTT 5.0                 |
+-----------------------------------------------------------+
```

**Key Technologies:**
- Ed25519 Identity | HMAC-SHA256 Signing | Hybrid Logical Clocks
- Sub-100ms latency | Byzantine Fault Tolerant (tolerates 1 of 4 nodes failing)
- Deterministic state convergence

---

## Slide 5: The Agent Economy in Action

### Economic Mechanism Design

| Phase | Action |
|-------|--------|
| **Discovery** | Agents auto-discover via retained MQTT announcements |
| **Negotiation** | Multi-round bidding (up to 3 rounds) with 3 strategies: Aggressive, Conservative, Adaptive |
| **Settlement** | 92% supplier / 3% logistics / 2% inspector / 3% burned |
| **Reputation** | Per-capability scoring (not global), decays toward neutral (0.5) |

### Bid Scoring Formula
```
score = 0.35 * price + 0.30 * reputation + 0.20 * speed + 0.15 * confidence
```

---

## Slide 6: Self-Healing Demonstration

### Failure Detection & Recovery

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

| Metric | Value |
|--------|-------|
| Heartbeat Interval | 5 seconds |
| Suspect Threshold | 15 seconds (3 missed) |
| Dead Threshold | 30 seconds (6 missed) |
| Recovery Ramp-up | 50% capacity for 2 epochs |

**Key Innovation:** Quorum-based confirmation prevents false positives from network partitions.

---

## Slide 7: Live Demo

### Laptop Supply Chain Crisis (3 Minutes)

| Time | Event |
|------|-------|
| t=8s | Buyer orders 50 laptop displays (max $120/unit) |
| t=50s | Buyer orders 100 laptop batteries (max $50/unit) |
| **t=70s** | **CHAOS: Supplier A crashes** |
| t=75s | Failure detected, quorum reached, roles redistributed |
| t=100s | Buyer orders 75 keyboards (max $30/unit) |
| **t=110s** | **RECOVERY: Supplier A rejoins at 50% capacity** |
| t=130s | Supplier A returns to full capacity |

**Dashboard:** Real-time agent states, order pipeline, ledger balances, event stream

---

## Slide 8: Performance Metrics

### Production-Ready Systems

| Metric | Value |
|--------|-------|
| **Test Coverage** | 152 tests (100 unit + 31 integration + 21 chaos) |
| **Operation Latency** | Sub-millisecond (agent-local) |
| **Consensus Latency** | ~50-100ms (FoxMQ Hashgraph) |
| **Self-Healing Time** | ~30s detection + redistribution |
| **Message Throughput** | 103K+ envelopes/sec |
| **Codebase** | ~2,500 lines Python + Svelte dashboard |

### Benchmarks (Apple Silicon)
```
canonical_json             0.0013 ms    762,000 ops/sec
envelope build + sign      0.0097 ms    103,000 ops/sec
full negotiation cycle     0.0038 ms    261,000 ops/sec
```

---

## Slide 9: SDK & Developer Experience

### Multi-Language Support

**Python Framework**
```python
from mesh.agents.buyer import BuyerAgent
from mesh.core.config import MeshConfig

config = MeshConfig(agent_role="buyer", capabilities=["electronics"])
agent = BuyerAgent(config)
agent.start()
```

**TypeScript SDK**
```typescript
import { Agent } from "@mesh/sdk";

const agent = new Agent({
  url: "wss://mesh.example.com",
  apiKey: "amk_...",
  role: "supplier",
  capabilities: ["displays", "batteries"]
});
await agent.connect();
```

**Deployment:** `docker compose up` - One command for full stack

---

## Slide 10: Real-World Applications

### Beyond the Hackathon

| Industry | Application |
|----------|-------------|
| **Warehouse Automation** | AMRs from different vendors coordinating picks without central WMS |
| **Drone Delivery** | Multi-operator fleets negotiating airspace and handoffs |
| **Disaster Response** | Search & rescue swarms operating with degraded connectivity |
| **Supply Chain** | Cross-company procurement without shared infrastructure |
| **Manufacturing** | Multi-vendor robotic workcells coordinating just-in-time production |

---

## Slide 11: Why We Win Track 3

### The Agent Economy Criteria

| Criteria | MESH Implementation |
|----------|-------------------|
| **Leaderless** | No master orchestrator - pure P2P negotiation via BFT-ordered MQTT |
| **Economic** | Full incentive-compatible mechanism: escrow, settlement, reputation, burn |
| **Autonomous** | Agents negotiate and execute at machine speed (sub-ms operations) |
| **Resilient** | Byzantine fault tolerance + self-healing with quorum confirmation |

### What Sets Us Apart
- **152 tests** - Systems over demos
- **Deterministic protocols** - Same BFT-ordered messages = identical state everywhere
- **Production architecture** - Not a prototype, a framework

---

## Slide 12: Technical Depth Highlights

### Advanced Distributed Systems

| Component | Innovation |
|-----------|-----------|
| **Hybrid Logical Clocks** | Causal ordering across topics, even with clock skew |
| **Per-Capability Reputation** | Trust per skill, not global; confidence weighting |
| **Deterministic Arbiter** | Dispute resolution without human intervention |
| **Double-Entry Ledger** | Escrow mechanism with deflationary burn |
| **Quorum-Based Healing** | Prevents false positives from network partitions |

**Security Model:**
- Ed25519 identity prevents impersonation
- HMAC-SHA256 signing prevents tampering
- Replay detector (10K nonce cache) prevents replay attacks
- BFT consensus tolerates malicious broker nodes

---

## Slide 13: Future Roadmap

### From Hackathon to Production

| Phase | Feature | Status |
|-------|---------|--------|
| **Now** | Core mesh framework | Complete |
| **Now** | Real-time dashboard | Complete |
| **Q2 2026** | Multi-tenant SaaS platform | In Progress (mesh_platform/) |
| **Q2 2026** | Payment gateway integration | In Progress (Cryptomus, Xendit) |
| **Q3 2026** | WASM agent runtime for edge devices | Planned |
| **Q3 2026** | Graph-based capability matching | Planned |
| **Q4 2026** | AI-powered negotiation strategies | Planned |

---

## Slide 14: Team & Acknowledgments

### Hitazurana

**Built on:**
- Tashi Vertex / FoxMQ - BFT-ordered MQTT with Hashgraph consensus

**Open Source:**
- MIT License
- github.com/[repository]

**Gratitude:**
- Tashi Network for the Vertex Swarm Challenge 2026
- The Hashgraph consensus research community

---

## Slide 15: Call to Action

### Experience MESH

**Run the Demo:**
```bash
git clone [repository]
cd Project-Vertex
docker compose up --build
# Dashboard at http://localhost:3000
```

**Explore the Code:**
- 2,500 lines of production Python
- SvelteKit real-time dashboard
- TypeScript SDK for browser/Node.js

**Contact:**
- Team: Hitazurana
- Track: 3 - The Agent Economy

---

## Appendix: Key Numbers for Judges

| Metric | Value |
|--------|-------|
| Agent roles | 5 (buyer, supplier, logistics, inspector, oracle) |
| Agent instances (demo) | 6 (2 competing suppliers) |
| FoxMQ nodes | 4 (BFT tolerates 1 faulty) |
| Protocol phases | 8 (discover to settle) |
| Message types | 22 Pydantic models |
| MQTT topics | 40+ (11 topic groups) |
| Negotiation strategies | 3 (aggressive, conservative, adaptive) |
| Counter-offer rounds | Up to 3 per order |
| Settlement split | 92/3/2/3 (supplier/logistics/inspector/burn) |
| Test count | 152 (all passing in ~0.10s) |
