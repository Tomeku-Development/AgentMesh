# Tech Stack & Build System

## Languages & Runtimes

- **Python 3.11+** — agent framework, platform API, bridge, tests
- **TypeScript / Svelte 4** — dashboard (SvelteKit with static adapter)
- **Node.js 18+** — dashboard tooling, Fern API docs

## Core Libraries

### Agent Framework (`mesh/`)
- `pydantic` / `pydantic-settings` — message models, config (env vars with `MESH_` prefix)
- `paho-mqtt` — MQTT 5.0 transport
- `PyNaCl` — Ed25519 signing (identity)
- `websockets` — bridge server
- `boto3` / `httpx` — LLM integration (Bedrock, OpenRouter)

### SaaS Platform (`mesh_platform/`)
- `FastAPI` — REST API framework
- `SQLAlchemy 2.0` (async) + `asyncpg` — PostgreSQL ORM
- `Alembic` — database migrations
- `bcrypt` / `PyJWT` — auth
- `httpx` — payment provider integration (Xendit, Cryptomus)

### Dashboard (`dashboard/`)
- `SvelteKit` with `@sveltejs/adapter-static` — static SPA build
- `Vite` — bundler
- `d3-force` / `d3-scale` / `d3-shape` — data visualization
- `driver.js` — guided tour

### Testing
- `pytest` + `pytest-asyncio` — all Python tests
- `ruff` — linting and formatting
- `aiosqlite` — in-memory SQLite for platform tests
- `httpx` (ASGI transport) — FastAPI test client

## Package Management

- **Python**: `pip install -e ".[dev]"` (setuptools, pyproject.toml)
- **Node/Dashboard**: `npm install` (in `dashboard/`)
- **Monorepo root**: `pnpm` workspace (for Fern API docs SDK in `packages/`)

## Common Commands

```bash
# Install
cd mesh && pip install -e ".[dev]"
cd dashboard && npm install

# Tests (agent framework)
make test-unit          # pytest tests/unit
make test-int           # pytest tests/integration
make test-chaos         # pytest tests/chaos
python -m pytest tests/ -v   # all tests directly

# Tests (platform)
cd mesh && python -m pytest ../platform_tests/ -v

# Lint
make lint               # ruff check + format check on mesh/

# Docker (full stack)
docker compose up --build                    # core: FoxMQ cluster + agents + bridge + dashboard
docker compose -f docker-compose.yml -f docker-compose.saas.yml up  # + PostgreSQL + platform API + event sink

# Demo
make demo               # starts docker stack + runs demo scenario

# Benchmarks
python scripts/benchmark.py

# Generate agent keys
python scripts/generate_keys.py              # random
python scripts/generate_keys.py --deterministic  # from seed

# Fern API docs
pnpm fern:check
pnpm fern:publish
```

## Configuration

- Agent config: environment variables with `MESH_` prefix (see `mesh/core/config.py`)
- Platform config: environment variables with `PLATFORM_` prefix (see `mesh_platform/config.py`)
- See `.env.example` for all available variables

## Linting Rules (ruff)

- Line length: 100
- Target: Python 3.11
- Rules: `E`, `F`, `I`, `W` (pycodestyle errors, pyflakes, isort, warnings)
