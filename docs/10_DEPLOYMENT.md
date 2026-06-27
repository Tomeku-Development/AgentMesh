# Deployment

# AgentMesh

**Version:** 1.0.0

**Status:** Deployment & Infrastructure Specification

**Developed by:** Tomeku

**Website:** https://tomeku.com

**Socials**

* Facebook: OfficialTomeku
* X: OfficialTomeku
* YouTube: OfficialTomeku

---

# Table of Contents

1. Overview
2. Environments
3. Topology
4. Frontend Deployment
5. Backend Deployment
6. Data Services
7. Blockchain Services
8. Secrets & Configuration
9. CI/CD Pipeline
10. Observability
11. Scaling Strategy
12. Backup & Disaster Recovery
13. Security Hardening
14. Cost Model
15. Release Checklist

---

# Overview

AgentMesh is deployed as a set of independently scalable services:

* A **Next.js** frontend (website + dashboard).
* A **FastAPI** gateway and orchestration backend (LangGraph).
* Stateful data services: **PostgreSQL**, **Redis**, **Qdrant**.
* **Casper** blockchain connectivity (Testnet → Mainnet).

The deployment philosophy is **stateless app tier, managed state tier**: application containers can be replaced at any time, while data lives in managed, backed-up services.

---

# Environments

| Environment | Purpose | Branch | Network |
|-------------|---------|--------|---------|
| `local` | Developer machines | any | Casper Testnet / mock |
| `preview` | Per-PR ephemeral previews | PR branches | Casper Testnet |
| `staging` | Pre-production validation | `develop` | Casper Testnet |
| `production` | Live platform | `main` | Casper Mainnet |

Each environment has isolated databases, secrets, and wallets. No environment shares a private key.

---

# Topology

```text
                         ┌─────────────────────────┐
                         │        Users / API       │
                         └────────────┬─────────────┘
                                      ▼
                            ┌──────────────────┐
                            │   Vercel (CDN)    │  Next.js frontend
                            └─────────┬─────────┘
                                      ▼  HTTPS
                            ┌──────────────────┐
                            │  FastAPI Gateway  │  Fly.io / Railway
                            └─────────┬─────────┘
                ┌─────────────────────┼─────────────────────┐
                ▼                     ▼                     ▼
        ┌──────────────┐     ┌───────────────┐     ┌───────────────┐
        │ LangGraph     │     │   PostgreSQL   │     │     Redis      │
        │ Orchestrator  │     │  (Neon/RDS)    │     │ (queue/cache)  │
        └──────┬────────┘     └───────────────┘     └───────────────┘
               ▼                       │
        ┌──────────────┐               ▼
        │    Qdrant     │       ┌───────────────┐
        │  (vectors)    │       │ Casper Network │
        └──────────────┘        └───────────────┘
```

---

# Frontend Deployment

* **Platform:** Vercel.
* **Framework:** Next.js 16 (App Router), React 19, Tailwind v4, shadcn/ui.
* **Build:** `next build` (Turbopack). Static landing pages are prerendered; dashboard routes are dynamic.
* **Images:** Next/Image optimization, WebP/AVIF, responsive `srcset`.
* **Edge:** Static assets and marketing pages served from the CDN edge.
* **Env:** `DATABASE_URL`, `NEXT_PUBLIC_API_URL`, analytics keys via Vercel project settings.

---

# Backend Deployment

* **Platform:** Fly.io (primary) or Railway.
* **Runtime:** Python 3.12, FastAPI, served by Uvicorn/Gunicorn workers.
* **Orchestration:** LangGraph workflow engine; long-running tasks via Celery or Temporal workers.
* **Containerization:** Docker multi-stage build, pinned base image, non-root user.
* **Health:** `/health` (liveness) and `/ready` (dependencies) endpoints used by the platform load balancer.
* **Autoscale:** Horizontal scaling on CPU and request concurrency.

---

# Data Services

| Service | Provider | Notes |
|---------|----------|-------|
| PostgreSQL | Neon / AWS RDS | Primary + read replica, PITR enabled |
| Redis | Upstash / managed | Queues, rate limiting, cache, sessions |
| Qdrant | Qdrant Cloud | Agent long-term memory & semantic search |

Migrations are managed with **Drizzle** (`db:migrate`) and run as a release step, never at request time.

---

# Blockchain Services

* **Network:** Casper Testnet (staging), Casper Mainnet (production).
* **Contracts:** Odra smart contracts deployed via CI with a dedicated deployer key.
* **Node access:** CSPR.cloud RPC endpoints.
* **Agent wallets:** Each agent has a scoped key managed by the backend KMS; spending limits enforced on-chain and off-chain.
* **MCP / x402:** Casper MCP server for tool access; x402 for machine-to-machine payments.

---

# Secrets & Configuration

* Secrets are stored in the platform secret manager (Vercel/Fly secrets) and never committed.
* Private keys live in a dedicated KMS / HSM; the application receives signing capability, not raw keys, where possible.
* Configuration follows 12-factor: all environment-specific values come from env vars.
* `.env.example` documents required variables; `.env*` files are git-ignored.

---

# CI/CD Pipeline

```text
push / PR
   │
   ▼
[1] Install + cache deps
   │
   ▼
[2] Lint  →  Type check  →  Unit tests
   │
   ▼
[3] Build (frontend + backend images)
   │
   ▼
[4] PR preview deploy (Vercel + ephemeral backend)
   │
   ▼  (merge to develop)
[5] Deploy staging  →  run db migrations  →  smoke tests
   │
   ▼  (merge to main)
[6] Deploy production (canary)  →  health gate  →  full rollout
```

* Tooling: GitHub Actions.
* Gates: build, type check, and tests must pass before any deploy.
* Rollback: previous immutable image/redeploy; database migrations are backward-compatible (expand/contract pattern).

---

# Observability

| Concern | Tool |
|---------|------|
| Errors | Sentry |
| Metrics | Prometheus / platform metrics |
| Dashboards | Grafana |
| Logs | Structured JSON, centralized aggregation |
| Tracing | OpenTelemetry across gateway → agents |
| Uptime | External status checks on `/health` |

Every agent run emits a trace so a decision can be reconstructed end-to-end.

---

# Scaling Strategy

* **Frontend:** edge CDN, effectively infinite static scale.
* **Gateway:** horizontal autoscale behind a load balancer.
* **Agents/workers:** queue-based; scale workers with backlog depth.
* **PostgreSQL:** read replicas for dashboards; connection pooling (PgBouncer).
* **Qdrant:** sharded collections for large memory stores.
* **Idempotency:** all on-chain executions are idempotent and keyed to avoid double-spend on retries.

---

# Backup & Disaster Recovery

| Asset | Strategy | Target |
|-------|----------|--------|
| PostgreSQL | Continuous PITR + daily snapshot | RPO ≤ 5 min |
| Qdrant | Scheduled snapshots | RPO ≤ 24 h |
| Secrets/keys | KMS managed, escrowed recovery | — |
| Contracts | Versioned, reproducible deploys | — |

Recovery objective: **RTO ≤ 1 hour** for the full stack. DR procedures are rehearsed before mainnet launch.

---

# Security Hardening

* HTTPS everywhere; HSTS enabled.
* Least-privilege IAM for every service.
* WAF + rate limiting at the gateway.
* Dependency and container scanning in CI.
* No raw secrets in logs; PII redaction.
* See `09_SECURITY.md` for the full threat model and controls.

---

# Cost Model

Indicative monthly ranges (staging-scale):

| Layer | Service | Est. cost |
|-------|---------|-----------|
| Frontend | Vercel Pro | $20+ |
| Backend | Fly.io / Railway | $25–100 |
| PostgreSQL | Neon | $0–69 |
| Redis | Upstash | $0–20 |
| Qdrant | Qdrant Cloud | $0–50 |
| AI APIs | OpenAI/Anthropic/Gemini | usage-based |

Costs scale primarily with AI token usage and agent activity, not infrastructure.

---

# Release Checklist

- [ ] Tests, lint, and type checks green
- [ ] DB migrations reviewed and backward-compatible
- [ ] Secrets present in target environment
- [ ] Smart contracts deployed to target network
- [ ] Smoke test: create org → submit → consensus → on-chain tx → dashboard
- [ ] Observability dashboards live
- [ ] Rollback path verified
- [ ] Stakeholder sign-off

---

**Built for the Casper Agentic Buildathon — by Tomeku.**
