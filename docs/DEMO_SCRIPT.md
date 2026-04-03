# MESH Demo Script

## Scenario: Laptop Supply Chain Crisis

A buyer needs laptop components (displays, batteries, keyboards) from competing suppliers. Mid-scenario, a supplier crashes and the swarm self-heals. This demonstrates all MESH capabilities in 3 minutes.

## Prerequisites

### Option A: Full Docker deployment (recommended for judges)

```bash
docker compose up --build -d
```

Wait for health checks to pass (~30 seconds). Then open the dashboard:
- **Dashboard**: http://localhost:3000
- **WebSocket bridge**: ws://localhost:8080

### Option B: Local Python (for development)

Requires a running FoxMQ broker on localhost:1883.

```bash
cd mesh && pip install -e ".[dev]"
python scripts/run_demo.py
```

## Demo Timeline

### Minute 0:00 - 0:30 | System Startup + Discovery

**What happens:**
- 4-node FoxMQ BFT cluster forms consensus
- 6 agents start: 1 buyer, 2 suppliers, 1 logistics, 1 inspector, 1 oracle
- Each agent generates an Ed25519 identity and announces on `mesh/discovery/announce`
- Agents discover each other through retained MQTT messages
- Heartbeats begin flowing every 5 seconds
- Oracle publishes initial market prices

**On the dashboard:**
- 6 AgentCards appear with green "ACTIVE" status
- MetricsPanel shows initial balances:
  - Buyer: 10,000 MESH_CREDIT
  - Supplier A: 5,000 MESH_CREDIT
  - Supplier B: 5,000 MESH_CREDIT
  - Logistics: 2,000 MESH_CREDIT
  - Inspector: 2,000 MESH_CREDIT
  - Oracle: 1,000 MESH_CREDIT

**Talking points:**
- "Every agent has a unique cryptographic identity derived from Ed25519"
- "The FoxMQ cluster uses Hashgraph consensus -- all agents see messages in identical order"
- "No central server coordinates anything -- agents discover each other via MQTT"

---

### Minute 0:30 - 1:00 | Order #1: Laptop Displays

**What happens (t=8s):**
1. Buyer publishes `PurchaseOrderRequest`:
   - 50x laptop displays, max $120/unit, quality threshold 85%
2. Both suppliers bid within the 10-second bid window:
   - Supplier A: $105/unit (has displays in inventory, cost $85)
   - Supplier B: $115/unit (no displays, higher cost)
3. Buyer's `NegotiationEngine` evaluates bids using reputation-weighted scoring
4. If best bid > 95% of market ($100): buyer generates counter-offer
5. Adaptive strategy proposes ~$95/unit based on competition factor
6. After 1-2 rounds, buyer accepts Supplier A at ~$98/unit
7. Buyer locks $4,900 in escrow
8. Supplier A commits and begins fulfillment
9. Logistics bids on shipping, gets assigned
10. Transit: picked_up -> in_transit -> delivered
11. Inspector verifies quality (score ~0.92, passes)
12. Escrow released: Supplier A gets 92%, Logistics 3%, Inspector 2%, 3% burned

**On the dashboard:**
- OrderFlow shows progression through phases
- EventLog streams bid/counter/accept messages in real-time
- MetricsPanel updates balances after settlement
- Supplier A's reputation increases

**Talking points:**
- "The negotiation engine uses an adaptive strategy that adjusts based on competition"
- "Escrow ensures the buyer can't take goods without paying"
- "Per-capability reputation means trust is earned per skill, not globally"
- "The 3% burn creates deflationary pressure on the MESH_CREDIT economy"

---

### Minute 1:00 - 1:30 | Order #2: Batteries + SUPPLIER CRASH

**What happens (t=50s):**
1. Buyer publishes order for 100x laptop batteries, max $50/unit
2. Both suppliers bid (Supplier B has batteries, lower cost)
3. Negotiation proceeds, Supplier B wins at ~$38/unit

**CHAOS EVENT (t=70s): Supplier A crashes!**

4. Supplier A stops sending heartbeats
5. After 15 seconds: multiple agents detect Supplier A as SUSPECT
6. After 30 seconds: agents publish `HealthAlert` with severity `critical`
7. Two independent detectors agree -> quorum reached, death confirmed
8. Coordinator (longest-uptime peer) computes role redistribution
9. `RoleRedistribution` published: Supplier B assumes Supplier A's active capabilities

**On the dashboard:**
- Supplier A's AgentCard turns red: "DEAD"
- HealthAlert messages appear in EventLog
- RoleRedistribution message shows capability transfer
- Order #2 continues uninterrupted with Supplier B

**Talking points:**
- "Watch the heartbeat monitor -- Supplier A's heartbeats stop"
- "Failure detection requires quorum: 2+ agents must independently agree a peer is dead"
- "This prevents false positives from network glitches"
- "The longest-uptime peer automatically becomes coordinator for redistribution"
- "No human intervention needed -- the swarm self-heals"

---

### Minute 1:30 - 2:30 | Order #3: Keyboards + RECOVERY

**What happens (t=100s):**
1. Buyer orders 75x keyboards, max $30/unit
2. Only Supplier B can bid (Supplier A is still down)
3. With no competition, negotiation is less aggressive -- Supplier B gets better price
4. Order proceeds through full lifecycle

**RECOVERY EVENT (t=110s): Supplier A comes back!**

5. Supplier A re-announces with status `"rejoining"`
6. `RecoveryManager` starts recovery: 50% capacity for 2 epochs
7. Supplier A syncs missed ledger/reputation state from retained MQTT messages
8. After 2 epochs (~2 minutes): fully active

**On the dashboard:**
- Supplier A's AgentCard turns yellow: "REJOINING"
- Load indicator shows 50% maximum
- After 2 epochs, turns green: "ACTIVE"

**Talking points:**
- "Supplier A is back but operates at 50% capacity as a safety measure"
- "This prevents a flapping agent from destabilizing the system"
- "Retained MQTT messages let the recovering agent catch up on missed state"
- "After 2 epochs of stable operation, full capacity is restored"

---

### Minute 2:30 - 3:00 | Final Summary

**What the dashboard shows:**
- 3 orders completed successfully
- All balances updated (buyer spent ~$9,000, suppliers earned proportionally)
- Reputation scores reflect performance:
  - Supplier A: slightly lower (missed time during crash)
  - Supplier B: higher (consistent availability)
  - Logistics and Inspector: positive from successful service
- Transaction count: 15-20 ledger transactions
- Self-healing event: 1 crash detected, redistributed, and recovered

**Final talking points:**
- "3 complete order lifecycles in 3 minutes -- all fully decentralized"
- "The economy is self-regulating: reputation, escrow, and settlement are all peer-computed"
- "Byzantine fault tolerance from FoxMQ means even malicious broker nodes can't corrupt state"
- "152 tests verify every component, from crypto primitives to chaos recovery"

---

## Key Numbers for Judges

| Metric | Value |
|--------|-------|
| Agent roles | 5 (buyer, supplier, logistics, inspector, oracle) |
| Agent instances | 6 (2 competing suppliers) |
| FoxMQ nodes | 4 (BFT tolerates 1 faulty) |
| Protocol phases | 7 (request to settle) |
| Message types | 22 Pydantic models |
| MQTT topics | 40+ (11 topic groups) |
| Negotiation strategies | 3 (aggressive, conservative, adaptive) |
| Counter-offer rounds | Up to 3 per order |
| Self-healing time | ~30s detect + redistribute |
| Recovery ramp-up | 50% capacity for 2 epochs |
| Settlement split | 92% supplier, 3% logistics, 2% inspector, 3% burn |
| Test count | 152 (100 unit + 31 integration + 21 chaos) |
| Operation latency | Sub-millisecond (agent-local) |
| Codebase | ~2,500 lines Python + Svelte dashboard |

## Chaos Controls (Interactive)

If the dashboard's ChaosControls panel is available, judges can:
- **Kill Agent**: Stop heartbeats for any agent, triggering failure detection
- **Restart Agent**: Bring a dead agent back, demonstrating recovery protocol
- **Inject Delay**: Simulate network latency for specific agents

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Dashboard shows no agents | Check bridge is running: `docker compose logs bridge` |
| FoxMQ cluster won't start | Ensure ports 1883-1886 are free: `lsof -i :1883` |
| Agents can't connect | Check `MESH_BROKER_HOST` matches Docker service name |
| Tests fail with import errors | Run `cd mesh && pip install -e ".[dev]"` |
| Stale Python cache | Run `make clean` to clear `__pycache__` |
