<div align="center">
  <img src="./docs/assets/logo.png" width="170" alt="AgentMesh logo" />

  <h1>AgentMesh</h1>

  <p><strong>The Operating System for Autonomous Organizations</strong></p>

  <p>
    Build, orchestrate, and deploy collaborative AI agents that reason,
    coordinate, and execute trusted on-chain actions on the Casper Network.
  </p>

  <p>
    <img alt="Next.js" src="https://img.shields.io/badge/Next.js-16-000?logo=nextdotjs" />
    <img alt="React" src="https://img.shields.io/badge/React-19-149ECA?logo=react&logoColor=white" />
    <img alt="TypeScript" src="https://img.shields.io/badge/TypeScript-5-3178C6?logo=typescript&logoColor=white" />
    <img alt="PostgreSQL" src="https://img.shields.io/badge/PostgreSQL-Drizzle-4169E1?logo=postgresql&logoColor=white" />
    <img alt="Casper" src="https://img.shields.io/badge/Built%20on-Casper-FF6A00" />
    <img alt="License" src="https://img.shields.io/badge/License-Apache%202.0-blue" />
  </p>
</div>

---

## Table of Contents

- [Overview](#overview)
- [Vision &amp; Mission](#vision--mission)
- [Why AgentMesh](#why-agentmesh)
- [How It Works](#how-it-works)
- [What's in This Repository](#whats-in-this-repository)
- [The Web App &amp; CMS](#the-web-app--cms)
- [Quick Start](#quick-start)
- [Environment Variables](#environment-variables)
- [Scripts](#scripts)
- [Architecture](#architecture)
- [Technology Stack](#technology-stack)
- [Roadmap](#roadmap)
- [Documentation](#documentation)
- [Contributing](#contributing)
- [License](#license)

---

## Overview

AgentMesh is a decentralized multi-agent orchestration platform that lets
organizations build autonomous AI teams capable of collaborating, making
decisions, and executing verifiable actions on-chain.

Unlike traditional AI assistants that operate alone, AgentMesh lets specialized
agents work together as an intelligent organization. Each agent has a dedicated
responsibility, memory, permissions, and wallet — enabling complex workflows such as:

- Venture Capital Due Diligence
- Treasury Management
- DAO Governance
- Compliance Automation
- Real-World Asset Verification
- Autonomous Procurement
- Multi-Agent Research
- Financial Decision Making

It combines modern AI orchestration with Casper smart contracts to deliver
transparency, auditability, and trust.

---

## Vision &amp; Mission

**Vision** — The future of organizations is autonomous. Software should no
longer simply assist people; it should reason, collaborate, negotiate, execute,
and verify. AgentMesh turns isolated AI assistants into collaborative digital
organizations that make trustworthy decisions.

**Mission** — Become the infrastructure layer for autonomous organizations by
combining multi-agent AI, blockchain, verifiable execution, transparent
governance, and decentralized trust.

---

## Why AgentMesh

Today's AI applications are mostly single-agent systems — they answer questions,
generate text, and write code. But real organizations need many specialists
working together. A CEO doesn't perform legal reviews; a lawyer doesn't manage
treasury. **Organizations succeed because specialists collaborate.** AgentMesh
brings that model to AI.

| Problem | AgentMesh |
| --- | --- |
| **Human bottlenecks** — meetings, approvals, manual coordination | Agents coordinate through a shared workflow engine |
| **Expensive expertise** across legal, finance, compliance | Specialized agents contribute on demand |
| **Fragmented AI** that can't collaborate | A coordinated mesh reaches consensus |
| **Lack of transparency** in decisions | Every critical action is recorded on Casper |
| **Limited automation** — AI recommends but rarely executes | Agents execute via smart contracts, with human oversight |

---

## How It Works

A request enters the mesh, specialists analyze it in parallel, a consensus
engine resolves it, and approved actions execute on-chain — leaving an immutable
audit trail.

```text
Startup Submission
        │
        ▼
   Coordinator Agent
        │
 ┌──────┼───────┬───────┐
 ▼      ▼       ▼       ▼
Market Finance Legal  GitHub
Agent   Agent  Agent   Agent
        │
        ▼
   Risk Analysis
        │
        ▼
   Consensus Engine
        │
        ▼
   Treasury Agent
        │
        ▼
 Casper Smart Contract
        │
        ▼
 Immutable Audit Trail
```

### Core principles

- **Specialized intelligence** — every agent owns a single responsibility.
- **Transparent reasoning** — every recommendation carries evidence.
- **Collaborative decisions** — agents debate before consensus.
- **On-chain trust** — critical actions are permanently recorded on Casper.
- **Human oversight** — organizations stay in control while delegating execution.

---

## What's in This Repository

This is the product monorepo for AgentMesh.

```text
Casper-Project/
├── web/        # Next.js 16 web app — marketing site, CMS, admin, docs, auth
├── docs/       # Full product & engineering documentation (20 documents)
├── Images/     # Brand assets (AgentMesh + Casper wordmarks, hero artwork)
└── README.md   # You are here
```

- **`web/`** — the live application: the public marketing site, a role-based
  admin/CMS, a documentation CMS, and BetterAuth authentication on PostgreSQL.
  See [`web/README.md`](./web/README.md) for full app docs.
- **`docs/`** — the canonical specification suite (PRD, architecture, database,
  API, agents, smart contracts, security, whitepaper, GTM, and more). Start at
  [`docs/README.md`](./docs/README.md).

> The full agent runtime (FastAPI + LangGraph) and Casper smart contracts are
> specified in `docs/` and are being implemented incrementally. The web app and
> its CMS/admin are live in `web/`.

---

## The Web App &amp; CMS

The `web/` app ships a complete, production-shaped front end:

- **Marketing site** — hero, multi-agent mesh diagram, features, how-it-works,
  pricing, solutions, agents, blog, and company pages.
- **Authentication** — email + password via **BetterAuth** on PostgreSQL, with
  roles (`admin` / `user`). The first account created becomes the admin.
- **Admin / CMS** (`/admin`) — Linear-meets-Vercel dashboard with KPIs, content
  editing, a documentation CMS, media library, network stats, subscribers and
  messages (with CSV export), users &amp; roles, and global SEO settings.
- **Documentation CMS** — Markdown-based docs with categories, per-page SEO
  metadata, and draft/publish, rendered at `/docs`.
- **Media** — image uploads to S3-compatible storage (Cloudflare R2 or Amazon S3).
- **Live data** — network stats, signups, and contact messages persist to
  PostgreSQL; everything degrades gracefully when the database is not configured.

---

## Quick Start

```bash
# from the repository root
cd web
npm install
cp .env.example .env.local   # then fill in values (see below)
npm run dev
```

Open <http://localhost:3000>. The site renders with sensible fallback data even
without a database. Visit `/admin` and create the first admin account.

To enable live data and the admin:

```bash
npm run db:push        # apply the schema to PostgreSQL
npm run db:seed        # seed initial network stats
npm run db:seed-docs   # (optional) seed starter documentation pages
```

---

## Environment Variables

Configured in `web/.env.local` (never committed). See `web/.env.example`.

| Variable | Required | Description |
| --- | --- | --- |
| `DATABASE_URL` | for live data | PostgreSQL connection string |
| `BETTER_AUTH_SECRET` | for auth | Long random string used to sign sessions |
| `BETTER_AUTH_URL` | prod | Public base URL (e.g. `https://agentmesh.world`) |
| `S3_BUCKET` | for uploads | Bucket name (R2 or S3) |
| `S3_ACCESS_KEY_ID` / `S3_SECRET_ACCESS_KEY` | for uploads | Credentials |
| `S3_REGION` | for uploads | `auto` for R2, or an AWS region |
| `S3_ENDPOINT` | R2 | R2 endpoint (omit for AWS) |
| `S3_PUBLIC_BASE_URL` | for uploads | Public URL objects are served from |

> **Security:** `.env.local` holds secrets (DB credentials, keys) and is
> git-ignored. Never commit it.

---

## Scripts

Run inside `web/`:

| Script | Description |
| --- | --- |
| `npm run dev` | Start the dev server |
| `npm run build` | Production build |
| `npm run start` | Run the production build |
| `npm run lint` | Lint the project |
| `npm run db:generate` | Generate SQL migrations from the schema |
| `npm run db:migrate` | Apply migrations |
| `npm run db:push` | Push schema directly (dev) |
| `npm run db:studio` | Open Drizzle Studio |
| `npm run db:seed` | Seed initial network stats |
| `npm run db:seed-docs` | Seed starter documentation pages |

---

## Deployment &amp; CI/CD

**Hosting (Vercel)** — the app lives in `web/`, so set the Vercel project's
**Root Directory** to `web`. Vercel auto-detects npm via `package-lock.json`
and deploys on every push (preview for PRs, production for `main`).

Configure these in the Vercel project (Production + Preview):

- `DATABASE_URL`, `BETTER_AUTH_SECRET`, `BETTER_AUTH_URL`
- `S3_BUCKET`, `S3_ACCESS_KEY_ID`, `S3_SECRET_ACCESS_KEY`, `S3_REGION`,
  `S3_ENDPOINT`, `S3_PUBLIC_BASE_URL`

> Use a **separate database** for Preview vs Production so PR deployments never
> touch production data. Never use the `NEXT_PUBLIC_` prefix for secrets.

**Continuous Integration (GitHub Actions)** — `.github/workflows/ci.yml` runs
on every push and PR to `main`: `npm ci` → `npm run lint` → `npm run build`.
This is the quality gate; Vercel handles the actual deploy (CD). The build uses
safe fallback data, so CI needs no secrets.

```text
push / PR ──▶ GitHub Actions (lint + build)        ── quality gate
push to main ─▶ Vercel (build + deploy production)  ── CD
open PR ──────▶ Vercel (preview deployment)         ── per-PR preview
```

---

## Architecture

```text
                 User / Browser
                       │
                       ▼
              Next.js (web app + CMS)
                       │
         ┌─────────────┼──────────────┐
         ▼             ▼              ▼
     PostgreSQL    BetterAuth     S3 / R2 media
   (Drizzle ORM)   (sessions)      (uploads)
         │
         ▼
   Planned: FastAPI Gateway → LangGraph Engine → Agents
                                   │
                                   ▼
                        Casper Smart Contracts → Casper Network
```

The web app and its data layer are implemented today. The agent runtime and
smart contracts are specified in `docs/` and integrate over the same data and
trust layer.

---

## Technology Stack

**Web app (this repo, live)**

- Next.js 16 (App Router), React 19, TypeScript
- Tailwind CSS v4, shadcn/ui, Lucide icons
- PostgreSQL + Drizzle ORM
- BetterAuth (email/password, roles)
- S3-compatible storage (Cloudflare R2 / Amazon S3)
- Markdown docs rendering (`marked`)

**Planned platform (specified in `docs/`)**

- Backend: FastAPI, LangGraph, Celery / Temporal, Redis
- Vector store: Qdrant
- AI: OpenAI, Anthropic, Google Gemini
- Blockchain: Casper Network, Odra smart contracts, Casper SDK, Casper MCP, CSPR.cloud, x402

---

## Roadmap

**Phase 1** — Multi-agent platform, Casper Testnet integration, Investment
Committee demo, organization dashboard.

**Phase 2** — Agent marketplace, custom organizations, workflow builder, team
collaboration.

**Phase 3** — Autonomous organizations, x402 payments, cross-agent commerce,
enterprise deployment.

See [`docs/11_ROADMAP.md`](./docs/11_ROADMAP.md) for the detailed roadmap.

---

## Documentation

The complete specification lives in [`docs/`](./docs/) — start at
[`docs/README.md`](./docs/README.md).

| # | Document | # | Document |
| --- | --- | --- | --- |
| 00 | [Overview](./docs/00_OVERVIEW.md) | 10 | [Deployment](./docs/10_DEPLOYMENT.md) |
| 01 | [Product Requirements](./docs/01_PRD.md) | 11 | [Roadmap](./docs/11_ROADMAP.md) |
| 02 | [System Architecture](./docs/02_SYSTEM_ARCHITECTURE.md) | 12 | [Pitch Deck](./docs/12_PITCH_DECK.md) |
| 03 | [Database Schema](./docs/03_DATABASE_SCHEMA.md) | 13 | [Demo Script](./docs/13_DEMO_SCRIPT.md) |
| 04 | [API Specification](./docs/04_API_SPEC.md) | 14 | [Whitepaper](./docs/14_WHITEPAPER.md) |
| 05 | [Agent Specification](./docs/05_AGENT_SPEC.md) | 15 | [Branding](./docs/15_BRANDING.md) |
| 06 | [Smart Contracts](./docs/06_SMART_CONTRACTS.md) | 16 | [Competitor Analysis](./docs/16_COMPETITOR_ANALYSIS.md) |
| 07 | [UI / UX](./docs/07_UI_UX.md) | 17 | [Go-To-Market](./docs/17_GO_TO_MARKET.md) |
| 08 | [Design System](./docs/08_DESIGN_SYSTEM.md) | 18 | [Casper Alignment](./docs/18_CASPER_ALIGNMENT.md) |
| 09 | [Security](./docs/09_SECURITY.md) | 19 | [Tokenomics](./docs/19_TOKENOMICS.md) |

---

## Contributing

We welcome contributions from developers, researchers, designers, and AI
engineers. Please read `CONTRIBUTING.md` and `CODE_OF_CONDUCT.md` before
submitting pull requests.

---

## License

Apache 2.0 — see [`LICENSE`](./LICENSE).

---

<div align="center">
  <sub>
    Built for the <strong>Casper Agentic Buildathon</strong> by
    <a href="https://tomeku.com">Tomeku</a> — together, building the operating
    system for autonomous organizations.
  </sub>
</div>
