# MESH - BUIDL Submission
## Vertex Swarm Challenge 2026

---

## Profile Section

### BUIDL (project) name
**MESH**

### BUIDL logo
*Upload a 480x480px PNG/JPEG logo (create a simple mesh/network icon or use the MESH text logo)*

### Vision
Centralized orchestrators are single points of failure. Multi-vendor robots cannot coordinate without proprietary middleware. When nodes fail, systems crash. Economic coordination requires trust without central authorities.

MESH eliminates the "Master Orchestrator" by enabling AI agents to autonomously negotiate, trade, ship, inspect, and settle supply chain orders at machine speed through BFT-ordered MQTT on Tashi Vertex/FoxMQ.

### Category
- [x] AI / Robotics
- [ ] Crypto / Web3
- [ ] Quantum Computing
- [ ] Space
- [ ] Other

---

## Details Section

### One-line description
Fully decentralized multi-agent supply chain coordination system with built-in economy, self-healing, and Byzantine fault tolerance.

### Problem statement
Current multi-agent systems rely on central orchestrators that:
- Create single points of failure
- Require vendor-specific middleware for coordination
- Cannot self-heal when nodes fail
- Lack economic mechanisms for trustless coordination

### Solution
MESH provides a pure peer-to-peer coordination layer where:
- **5 autonomous agent roles** (Buyer, Supplier, Logistics, Inspector, Oracle) negotiate without central control
- **BFT-ordered MQTT** via FoxMQ ensures deterministic state convergence across all agents
- **Self-healing protocol** detects failures, reaches quorum, and redistributes roles automatically
- **Built-in economy** with escrow, settlement splits (92/3/2/3), per-capability reputation, and deflationary burn

### Technical architecture
```
Dashboard (SvelteKit) ←→ WebSocket Bridge ←→ MQTT 5.0 ←→ FoxMQ BFT Cluster (4 nodes)
                                                           ↓
              ┌─────────┬─────────┬─────────┬─────────┐
              │  Buyer  │Supplier │Logistics│Inspector│
              └─────────┴─────────┴─────────┴─────────┘
                    ↓              ↓
              ┌─────────────────────────────────┐
              │  Ledger │Reputation│Negotiation│
              └─────────────────────────────────┘
```

**Key Technologies:**
- Tashi Vertex / FoxMQ (Hashgraph consensus, sub-100ms latency)
- Ed25519 identity, HMAC-SHA256 signing
- Hybrid Logical Clocks for causal ordering
- Double-entry ledger with escrow mechanism
- 152 tests (unit + integration + chaos)

### Demo video
*Upload a 3-minute screen recording showing:*
1. System startup with 6 agents discovering each other
2. Order placement and multi-round negotiation
3. Supplier crash at t=70s with self-healing
4. Recovery at t=110s with 50% capacity ramp-up
5. Final settlement with reputation updates

### Track
**Track 3: The Agent Economy**

### Track fit explanation
MESH directly addresses Track 3 requirements:
- **Leaderless**: No master orchestrator - pure P2P negotiation via BFT-ordered MQTT
- **Economic**: Full incentive-compatible mechanism design with escrow, settlement, reputation, and burn
- **Autonomous**: Agents make decisions at machine speed (sub-millisecond operations)
- **Resilient**: Byzantine fault tolerance + self-healing with quorum confirmation

### GitHub repository
`https://github.com/[your-username]/Project-Vertex`

### Live demo URL
`http://localhost:3000` (local deployment)

### Pitch deck
*Upload the PITCH_DECK.md or convert to PDF*

---

## Team Section

### Team name
**Hitazurana**

### Team members
- [Team member 1] - Role (e.g., Lead Developer)
- [Team member 2] - Role (e.g., Systems Architect)
- [Add more as needed]

### Team background
*Describe your team's experience with distributed systems, multi-agent coordination, and relevant technical expertise*

---

## Contact Section

### Email
*[Your team email]*

### Discord handle
*[Your Discord usernames for the team]*

### Twitter/X handle
*[Optional - your project or team Twitter]*

---

## Submission Section

### Project status
- [x] Working prototype with demo
- [ ] Concept/PoC only
- [ ] Production ready

### Additional materials
*Links to:*
- Architecture diagrams (ARCHITECTURE_DIAGRAM.md)
- Demo video script (DEMO_SCRIPT_VIDEO.md)
- One-pager summary (ONE_PAGER.md)

### How to run
```bash
# Prerequisites: Docker, Python 3.11+, Node.js 18+

# Clone repository
git clone https://github.com/[username]/Project-Vertex
cd Project-Vertex

# Option 1: Full Docker deployment (requires x86_64)
docker compose up --build

# Option 2: Local development (Apple Silicon compatible)
# Terminal 1: Start MQTT broker
docker run -d --name mosquitto -p 1883:1883 eclipse-mosquitto:2

# Terminal 2: Start WebSocket bridge
python3 -m bridge.server --mqtt-host 127.0.0.1 --mqtt-port 1883 --ws-port 8080

# Terminal 3: Start dashboard
cd dashboard && npm install && npm run dev

# Terminal 4: Run demo agents
python3 scripts/run_demo.py --host 127.0.0.1 --port 1883

# Access dashboard at http://localhost:3000
```

### Key metrics
| Metric | Value |
|--------|-------|
| Test coverage | 152 tests (100 unit + 31 integration + 21 chaos) |
| Operation latency | Sub-millisecond (agent-local) |
| Consensus latency | ~50-100ms (FoxMQ Hashgraph) |
| Message throughput | 103K+ envelopes/sec |
| Self-healing time | ~30s detection + redistribution |
| Codebase | ~2,500 lines Python + Svelte |

### What makes this unique
1. **True decentralization**: No single point of failure, no central coordinator
2. **Economic realism**: Incentive-compatible mechanism design with real consequences
3. **Production-ready**: 152 tests, deterministic protocols, sub-ms operations
4. **Vertex integration**: Deep FoxMQ integration showcasing BFT consensus power

### Future roadmap
- Multi-tenant SaaS platform (mesh_platform/ in progress)
- Payment gateway integration (Cryptomus, Xendit)
- WASM agent runtime for edge devices
- Graph-based capability matching

---

## Quick Reference for Form Fields

### For "Vision" field (short version):
MESH eliminates centralized orchestrators by enabling AI agents to autonomously negotiate, trade, and settle supply chain orders through BFT-ordered MQTT. With self-healing, built-in economy, and Byzantine fault tolerance, it's the TCP/IP for supply chain swarms.

### For "One-line description" field:
Fully decentralized multi-agent supply chain coordination with self-healing economy on Tashi Vertex.

### For "Track fit" field:
MESH is built for Track 3: The Agent Economy. It has no master orchestrator (pure P2P), features a complete economic system (escrow, settlement, reputation, burn), operates autonomously at machine speed, and self-heals through quorum-based failure detection.

### For "Problem statement" field:
Centralized orchestrators are single points of failure. Multi-vendor robots can't coordinate without proprietary middleware. Systems crash when nodes fail. Economic coordination lacks trust mechanisms.

### For "Solution" field:
MESH provides peer-to-peer coordination where 5 agent roles negotiate autonomously via BFT-ordered MQTT on FoxMQ. Features include self-healing with quorum confirmation, built-in economy with escrow/settlement/reputation, and deterministic state convergence.
