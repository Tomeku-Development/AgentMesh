# Project Structure

```
Project-Vertex/
├── mesh/                        # Python agent framework (installable package)
│   ├── core/                    # Foundational modules
│   │   ├── identity.py          # Ed25519 keypair management
│   │   ├── crypto.py            # HMAC-SHA256 signing, replay detection
│   │   ├── clock.py             # Hybrid Logical Clocks
│   │   ├── config.py            # Pydantic settings (MESH_ env prefix)
│   │   ├── messages.py          # 22 Pydantic message models
│   │   ├── protocol.py          # Envelope build/verify/serialize
│   │   ├── topics.py            # MQTT topic constants + QoS mapping
│   │   ├── state.py             # Agent FSM (8 states, validated transitions)
│   │   ├── registry.py          # Peer discovery registry
│   │   ├── ledger.py            # Double-entry ledger with escrow
│   │   ├── reputation.py        # Per-capability scoring engine
│   │   ├── transport.py         # MQTT transport layer
│   │   └── capability_utils.py  # Capability normalization
│   ├── agents/                  # Agent role implementations
│   │   ├── base.py              # BaseAgent ABC (lifecycle, heartbeat, dispatch)
│   │   ├── buyer.py             # Purchase order + negotiation logic
│   │   ├── supplier.py          # Bidding + fulfillment logic
│   │   ├── logistics.py         # Shipping lifecycle management
│   │   ├── inspector.py         # Quality inspection + reporting
│   │   └── oracle.py            # Market data publisher
│   ├── negotiation/             # Multi-round negotiation engine
│   │   ├── strategies.py        # Aggressive / Conservative / Adaptive
│   │   ├── engine.py            # Negotiation state machine
│   │   └── arbiter.py           # Deterministic dispute resolution
│   ├── healing/                 # Self-healing subsystem
│   │   ├── detector.py          # Heartbeat failure detection
│   │   ├── redistributor.py     # Role reassignment
│   │   └── recovery.py          # Capacity ramp-up manager
│   ├── scenarios/               # Demo scenarios
│   ├── llm/                     # LLM provider integration
│   ├── cli.py                   # Click CLI entry point
│   └── pyproject.toml           # Package config (setuptools)
│
├── mesh_platform/               # SaaS platform (FastAPI)
│   ├── app.py                   # Application factory
│   ├── config.py                # Platform settings (PLATFORM_ env prefix)
│   ├── dependencies.py          # FastAPI dependency injection
│   ├── routers/                 # API route handlers
│   │   ├── auth.py              # Registration, login, JWT
│   │   ├── workspaces.py        # Multi-tenant workspace CRUD
│   │   ├── orders.py            # Order management
│   │   ├── ledger.py            # Ledger queries
│   │   ├── agents.py            # Agent management
│   │   ├── payments.py          # Xendit + Cryptomus billing
│   │   ├── api_keys.py          # API key management
│   │   ├── capabilities.py      # Capability catalog
│   │   └── admin.py             # Admin endpoints
│   ├── models/                  # SQLAlchemy ORM models
│   ├── schemas/                 # Pydantic request/response schemas
│   ├── services/                # Business logic layer
│   ├── gateway/                 # WebSocket gateway
│   ├── sink/                    # MQTT event subscriber (writes to DB)
│   ├── migrations/              # Alembic DB migrations
│   └── payments/                # Payment provider integrations
│
├── platform/                    # Platform package config
│   ├── pyproject.toml           # Dependencies for mesh_platform
│   └── migrations/              # Additional migrations
│
├── bridge/                      # MQTT → WebSocket bridge
│   ├── server.py                # Bridge server
│   └── filters.py               # Topic filtering for dashboard
│
├── dashboard/                   # SvelteKit real-time UI
│   ├── src/
│   │   ├── lib/
│   │   │   ├── components/      # AgentCard, OrderFlow, MetricsPanel, EventLog, ChaosControls
│   │   │   ├── stores/          # Svelte stores (websocket, agents, orders, metrics, auth)
│   │   │   ├── api/             # Platform API client modules
│   │   │   ├── types/           # TypeScript type definitions
│   │   │   ├── tour/            # Guided tour (driver.js)
│   │   │   ├── demo/            # Demo engine + mock data
│   │   │   └── utils/           # Utility functions
│   │   └── routes/              # SvelteKit pages (/, /auth, /dashboard, /docs, /workspaces)
│   ├── svelte.config.js
│   └── vite.config.ts
│
├── tests/                       # Agent framework tests
│   ├── conftest.py              # Shared fixtures
│   ├── unit/                    # 100 tests — core + negotiation + reputation
│   ├── integration/             # 31 tests — discovery, order lifecycle, settlement
│   └── chaos/                   # 21 tests — self-healing, failure recovery
│
├── platform_tests/              # Platform API tests (async, SQLite in-memory)
│   ├── conftest.py              # DB engine, session, httpx client fixtures
│   ├── test_auth.py
│   ├── test_workspaces.py
│   ├── test_payments.py
│   └── ...
│
├── scripts/                     # Utility scripts
├── fern/                        # Fern API documentation config
├── foxmq/                       # FoxMQ broker Docker build
├── docs/                        # Protocol and demo documentation
│
├── docker-compose.yml           # Core stack (FoxMQ cluster + agents + bridge + dashboard)
├── docker-compose.saas.yml      # SaaS overlay (+ PostgreSQL + platform API + event sink)
├── Dockerfile.agent             # Python agent container
├── Dockerfile.platform          # Platform API container
├── Makefile                     # Build/test/deploy commands
└── pnpm-workspace.yaml          # pnpm workspace (packages/sdk)
```

## Key Patterns

- **Agent framework tests** live in `tests/` (run from `mesh/` directory)
- **Platform tests** live in `platform_tests/` (separate conftest with async SQLite)
- All agents extend `BaseAgent` ABC in `mesh/agents/base.py`
- All message types are Pydantic models in `mesh/core/messages.py`
- Platform API routes are in `mesh_platform/routers/`, business logic in `mesh_platform/services/`
- Platform uses FastAPI dependency injection (`mesh_platform/dependencies.py`) for DB sessions
