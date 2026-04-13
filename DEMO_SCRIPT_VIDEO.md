# MESH Demo Video Script
## "Laptop Supply Chain Crisis" - 3 Minutes

---

## Pre-Production Notes

- **Target Duration:** 3 minutes
- **Format:** Screen recording with voiceover
- **Resolution:** 1920x1080 (dashboard at full screen)
- **Background Music:** Optional, low volume electronic/ambient

---

## Scene 1: Introduction (0:00 - 0:15)

**Visual:**
- Terminal window showing `docker compose up --build` completing
- Transition to dashboard at http://localhost:3000
- Dashboard loads with dark theme, MESH logo

**Voiceover:**
> "MESH is a fully decentralized multi-agent supply chain system. No central orchestrator. Just autonomous agents negotiating, trading, and self-healing. Let me show you what that looks like."

**On-screen text:**
- "MESH: The TCP/IP for Supply Chain Swarms"
- "Track 3: The Agent Economy"

---

## Scene 2: System Startup (0:15 - 0:35)

**Visual:**
- Dashboard showing 6 AgentCards appearing one by one
- Agent statuses all turn green (ACTIVE)
- MetricsPanel populates with initial balances

**Voiceover:**
> "We start with a 4-node FoxMQ BFT cluster and 6 agents: a buyer, two competing suppliers, logistics, an inspector, and a market oracle. Each agent has a cryptographic Ed25519 identity. They discover each other automatically through retained MQTT messages."

**Highlight:**
- Mouse hovers over each AgentCard to show role and capabilities
- Show the connection badge: "LIVE"

---

## Scene 3: Order #1 - Laptop Displays (0:35 - 1:05)

**Visual:**
- EventLog starts scrolling
- OrderFlow shows new order appearing
- Bid messages appear in EventLog

**Voiceover:**
> "At 8 seconds, the buyer orders 50 laptop displays, max budget 120 dollars per unit. Both suppliers bid. Supplier A offers 105 dollars - they have displays in stock. Supplier B bids 115 - they'd need to source them."

**Visual:**
- OrderFlow transitions: REQUEST → BID → NEGOTIATE → COMMIT
- Counter-offer messages in EventLog

**Voiceover:**
> "The buyer's negotiation engine uses an adaptive strategy. It generates a counter-offer at 95 dollars based on competition. After one round, they agree on 98 dollars per unit. The buyer locks 4,900 dollars in escrow."

**Highlight:**
- Show escrow lock transaction in EventLog
- Supplier A's AgentCard shows "BUSY" status

---

## Scene 4: Order #2 - Batteries + CHAOS (1:05 - 1:45)

**Visual:**
- Second order appears in OrderFlow
- Bids come in from both suppliers

**Voiceover:**
> "At 50 seconds, the buyer orders 100 laptop batteries. This time Supplier B wins the bid - they have better battery inventory. Negotiation completes and the order commits."

**Visual:**
- **CRASH EVENT:** Supplier A's AgentCard turns red (DEAD)
- EventLog shows HealthAlert messages
- Other agents' cards show warning indicators briefly

**Voiceover:**
> "At 70 seconds - chaos. Supplier A crashes. Watch what happens. Heartbeats stop. After 15 seconds, agents mark Supplier A as suspect. After 30 seconds, multiple agents publish critical health alerts. Quorum is reached - two independent detectors agree. Supplier A is confirmed dead."

**Visual:**
- RoleRedistribution message appears in EventLog
- Supplier B's AgentCard shows increased load

**Voiceover:**
> "The longest-uptime peer automatically becomes coordinator and redistributes Supplier A's capabilities. No human intervention. The swarm self-heals."

---

## Scene 5: Order #3 - Keyboards + Recovery (1:45 - 2:25)

**Visual:**
- Third order appears: 75 keyboards
- Only Supplier B bids (no competition)

**Voiceover:**
> "At 100 seconds, the buyer orders 75 keyboards. With Supplier A down and only one bidder, the negotiation is less aggressive - Supplier B gets a better price. The order proceeds through fulfillment, shipping, inspection, and settlement."

**Visual:**
- **RECOVERY EVENT:** Supplier A's AgentCard turns yellow (REJOINING)
- EventLog shows DiscoveryAnnounce with "rejoining" status

**Voiceover:**
> "At 110 seconds - Supplier A comes back online. But notice: it rejoins at only 50 percent capacity. This safety measure prevents flapping agents from destabilizing the system. After 2 epochs of stable operation, it returns to full active status."

**Visual:**
- Supplier A's card transitions: REJOINING → ACTIVE
- Load indicator shows 100%

---

## Scene 6: Final Summary (2:25 - 3:00)

**Visual:**
- Full dashboard view
- All 3 orders show "SETTLED" in OrderFlow
- MetricsPanel shows final balances and transaction counts

**Voiceover:**
> "In 3 minutes, we completed 3 full order lifecycles, processed a supplier crash with automatic recovery, and settled nearly 10,000 dollars in MESH credits. Every transaction was cryptographically signed. Every decision was made autonomously. Every state change was replicated across all agents through BFT consensus."

**Visual:**
- Zoom into MetricsPanel showing:
  - 152 tests passing
  - Sub-millisecond operation latency
  - 103K messages per second throughput

**Voiceover:**
> "This isn't a demo. It's a production framework with 152 tests, sub-millisecond agent operations, and Byzantine fault tolerance. MESH is the coordination layer for the agent economy."

**Final Screen:**
- MESH logo
- "github.com/[repository]"
- "Team: Hitazurana"
- "Track 3: The Agent Economy"

---

## Technical Notes for Recording

### Setup Commands
```bash
# Terminal 1: Start the infrastructure
docker compose up --build

# Wait for all services healthy (~30 seconds)
# Dashboard will be at http://localhost:3000
```

### Recording Checklist
- [ ] Close all unnecessary applications
- [ ] Set screen resolution to 1920x1080
- [ ] Hide desktop icons
- [ ] Use clean browser profile (no extensions visible)
- [ ] Test audio levels before recording
- [ ] Record in a quiet environment

### Post-Production
- [ ] Trim silence at beginning/end
- [ ] Add subtle background music (optional)
- [ ] Add captions for key metrics
- [ ] Export as 1080p MP4 (H.264)

---

## Key Talking Points (for reference)

1. **No central orchestrator** - All coordination through BFT-ordered MQTT
2. **Deterministic state** - Same messages = identical state everywhere
3. **Economic realism** - Escrow, settlement splits, reputation, burn
4. **Self-healing** - Quorum-based failure detection and recovery
5. **Production-ready** - 152 tests, sub-ms latency, 100K+ msg/sec

---

## Alternative: 60-Second Elevator Pitch Version

**Scene 1 (0:00-0:10):** Dashboard with all agents active
> "MESH is decentralized supply chain coordination. 6 agents, zero central orchestrator."

**Scene 2 (0:10-0:25):** Show order flow with bids and negotiation
> "Agents negotiate prices, lock escrow, and settle autonomously."

**Scene 3 (0:25-0:40):** CHAOS - Supplier A crashes
> "When a supplier crashes, the swarm detects it, reaches quorum, and redistributes roles."

**Scene 4 (0:40-0:50):** Recovery and final state
> "The agent recovers at reduced capacity and rejoins the economy."

**Scene 5 (0:50-60):** Metrics panel
> "152 tests. Sub-millisecond operations. This is the agent economy."
