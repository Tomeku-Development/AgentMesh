# Product Overview

MESH is a decentralized multi-agent supply chain coordination system built for the Vertex Swarm Challenge 2026 (Track 3: Agent Economy).

Autonomous agents (Buyer, Supplier, Logistics, Inspector, Oracle) negotiate, trade, ship, inspect, and settle supply chain orders with no central orchestrator. All coordination happens through BFT-ordered MQTT messages on a FoxMQ Hashgraph cluster, achieving deterministic state convergence across all agents.

## Key Concepts

- **No central orchestrator** — agents coordinate purely via pub/sub MQTT topics
- **Deterministic state** — BFT ordering guarantees identical state on every agent
- **Ed25519 identity** — each agent has a cryptographic keypair; `agent_id = SHA-256(pubkey)[:16]`
- **MESH_CREDIT currency** — in-memory double-entry ledger with escrow, settlement splits, and 3% deflationary burn
- **Per-capability reputation** — scores per skill (not global), decay toward neutral (0.5)
- **Self-healing** — heartbeat failure detection, quorum confirmation, role redistribution, 50% capacity recovery ramp-up
- **Protocol phases**: `DISCOVER → REQUEST → BID → NEGOTIATE → COMMIT → EXECUTE → VERIFY → SETTLE`

## Two Layers

1. **Agent Framework** (`mesh/`) — the core P2P agent system (Python)
2. **SaaS Platform** (`mesh_platform/`) — enterprise control plane with multi-tenant workspaces, auth, billing, and a REST API (FastAPI + PostgreSQL)

## Agent Roles

| Role | Responsibilities |
|------|-----------------|
| Buyer | Publishes purchase orders, evaluates bids, negotiates prices, locks escrow |
| Supplier | Bids on orders, fulfills committed orders, manages inventory and costs |
| Logistics | Bids on shipping requests, handles pickup/transit/delivery lifecycle |
| Inspector | Performs quality inspection, issues pass/partial/reject reports |
| Oracle | Publishes market prices and demand forecasts each epoch |
