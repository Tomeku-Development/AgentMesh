# AgentMesh

Landing site for **AgentMesh** — the decentralized operating system for
autonomous organizations, built on the Casper Network.

Built with **Next.js 16 (App Router)**, **React 19**, **Tailwind CSS v4**,
**shadcn/ui**, and **PostgreSQL** via **Drizzle ORM**.

## Quick start

```bash
npm install
npm run dev
```

Open http://localhost:3000. The site renders fully with built-in fallback data
even without a database connection.

## Database (PostgreSQL)

The database is optional for local preview but powers live network stats and
captures newsletter signups + contact submissions.

1. Create a Postgres database and set the connection string in `.env.local`:

   ```env
   DATABASE_URL="postgresql://USER:PASSWORD@localhost:5432/agentmesh"
   ```

2. Apply the schema (choose one):

   ```bash
   npm run db:push       # push schema directly (great for dev)
   # or
   npm run db:migrate    # run the generated SQL migrations
   ```

3. Seed initial network stats:

   ```bash
   npm run db:seed
   ```

### Database scripts

| Script              | Description                                  |
| ------------------- | -------------------------------------------- |
| `npm run db:generate` | Generate SQL migrations from the schema    |
| `npm run db:migrate`  | Apply generated migrations                 |
| `npm run db:push`     | Push the schema directly (no migration)    |
| `npm run db:studio`   | Open Drizzle Studio                        |
| `npm run db:seed`     | Insert an initial `network_stats` row      |

## Project structure

```
src/
├─ app/
│  ├─ actions/subscribe.ts   # server action → writes subscribers to Postgres
│  ├─ layout.tsx             # fonts + metadata
│  ├─ page.tsx               # landing page composition
│  └─ globals.css            # dark theme + Casper-orange tokens
├─ components/
│  ├─ site/                  # navbar, hero, stats, features, how-it-works, cta, footer
│  └─ ui/                    # shadcn/ui primitives
└─ lib/
   ├─ db/                    # Drizzle schema, client, seed
   ├─ data/stats.ts          # network stats query w/ graceful fallback
   ├─ content.ts             # nav / features / steps / agents content
   └─ format.ts              # number formatting helpers
```

## Schema

- **network_stats** — agents online, transactions, proposals, TVL (CSPR)
- **subscribers** — newsletter / early-access emails (unique)
- **contact_submissions** — contact form messages
- **site_content** — editable marketing copy (key/value)
- **media_assets** — uploaded image metadata + public URL

## Brand assets

Logos and the hero artwork live in `public/images/` (AgentMesh wordmarks,
Casper wordmarks, and the hero background).

## Pages

All navigation and footer links resolve to real routes:

| Section | Routes |
| --- | --- |
| Platform | `/platform`, `/platform/multi-agent-mesh`, `/platform/on-chain-trust`, `/pricing` |
| Top-level | `/solutions`, `/agents`, `/docs`, `/docs/api`, `/sdks` |
| Company | `/about`, `/blog`, `/blog/[slug]`, `/careers`, `/contact` |
| Legal / status | `/privacy`, `/terms`, `/status` |

The navbar (Platform, Developers, Company) uses dropdown menus with active-state
highlighting; GitHub opens externally. Navbar and footer are global (rendered in
`app/layout.tsx`).

## API & backend

| Endpoint | Description |
| --- | --- |
| `GET /api/health` | Service health + live PostgreSQL connectivity probe |
| `GET /api/stats` | Live network stats (falls back to defaults without a DB) |

Backend-connected features:

- **Contact** (`/contact`) — server action writes to `contact_submissions`.
- **Newsletter** (home CTA) — server action writes to `subscribers`.
- **Status** (`/status`) — reads health + network stats on every request.

All backend features degrade gracefully: without `DATABASE_URL` the forms still
succeed and the status page reports the database as "not configured".

## Admin panel (`/admin`)

A role-based admin (BetterAuth + Postgres) manages content, docs, media, and users.

- **Auth:** email + password via [BetterAuth](https://better-auth.com), sessions in Postgres.
- **First run:** visit `/admin/login` — with no users yet it shows "Create the
  first admin"; that first account becomes an **admin**. Everyone created after
  defaults to **user**.
- **Roles:** only `admin` users can access `/admin`. Manage users at
  `/admin/users` (invite, promote/demote, ban, delete).
- Set `BETTER_AUTH_SECRET` (and `BETTER_AUTH_URL` in production).

| Section | Path | What it does |
| --- | --- | --- |
| Overview | `/admin` | KPIs, sparklines, activity, system status |
| Pages & Content | `/admin/content` | Edit hero/CTA copy |
| Documentation | `/admin/docs` | Write/publish docs (Markdown + SEO) |
| Media | `/admin/media` | Upload, copy URL, delete (S3/R2) |
| Subscribers | `/admin/subscribers` | View + **export CSV** |
| Messages | `/admin/messages` | View + **export CSV** |
| Network Stats | `/admin/stats` | Edit live stats |
| Users & Roles | `/admin/users` | Manage accounts and roles |
| Settings | `/admin/settings` | Global site identity + default SEO |

## Documentation CMS

Docs live in the `doc_pages` table and render at `/docs` (index) and
`/docs/[slug]` (Markdown, with a category sidebar and per-page SEO metadata).
Drafts stay hidden until published. Seed starter docs with:

```bash
npm run db:seed-docs
```

> `/docs/api` is a reserved static route, so `api` cannot be used as a doc slug.

## Media storage (Cloudflare R2 or Amazon S3)

Uploads go to any S3-compatible bucket. Configure via env (see `.env.example`):

```env
S3_BUCKET=...
S3_ACCESS_KEY_ID=...
S3_SECRET_ACCESS_KEY=...
S3_REGION=auto                 # "auto" for R2, e.g. us-east-1 for AWS
S3_ENDPOINT=https://<acct>.r2.cloudflarestorage.com   # omit for AWS
S3_PUBLIC_BASE_URL=https://media.example.com           # public object URL base
S3_FORCE_PATH_STYLE=true       # recommended for R2
```

Uploaded files are streamed through `POST /api/admin/media` (auth-protected),
stored in the bucket, and tracked in the `media_assets` table. Without storage
configured, the rest of the admin still works and the uploader shows a setup
notice.

## Notes

- The stats bar reads from `network_stats`; if the DB is unset or empty it
  falls back to representative values so the page never breaks.
- The site is dark-themed by default to match the AgentMesh brand.
