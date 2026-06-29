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
| Promotion | `/presentation?video=<youtube-id-or-url>` |

The navbar (Platform, Developers, Company) uses dropdown menus with active-state
highlighting; GitHub opens externally. Navbar and footer are global (rendered in
`app/layout.tsx`).

## Presentation Mode

`/presentation` is a full-screen promotional video experience. Configure the
default video and countdown copy from `/admin/settings` under the
`Presentation` group, set `NEXT_PUBLIC_PRESENTATION_YOUTUBE_ID`, or pass a
YouTube ID/URL in the query:

```text
/presentation?video=YOUR_VIDEO_ID
```

Browsers require a click before fullscreen can start, so the page opens with a
launch control. When the video ends, it runs a racing-style countdown and then
redirects to `/`, with controls to replay or skip immediately.

## API & backend

| Endpoint | Description |
| --- | --- |
| `GET /api/health` | Service health + live PostgreSQL connectivity probe |
| `GET /api/stats` | Live network stats (falls back to defaults without a DB) |
| `POST /api/checkout` | Creates hosted Pro checkout via Xendit, Stripe, or Polar |
| `POST /api/payments/webhook/[provider]` | Records provider payment status callbacks |

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
- **Two-factor auth:** admins can enable authenticator-app TOTP from
  `/admin/account`. Sign-in then redirects to `/admin/two-factor` for the
  second factor. Backup codes are shown once during setup.
- **Passkeys:** admins can add Touch ID, Face ID, Windows Hello, or hardware
  security keys from `/admin/account`, then use them on `/admin/login`.
- **API keys:** admins can create local API keys from `/admin/account`.
  Generated keys are hashed at rest and shown only once.
- **Organizations:** the Better Auth organization plugin is enabled at
  `/admin/organization`; only admins can create organizations.
- **Last login method:** Better Auth records the last login method and shows it
  in the account session details.
- Set `BETTER_AUTH_SECRET` (and `BETTER_AUTH_URL` in production).
- In production, set `BETTER_AUTH_URL=https://www.agentmesh.world` and, if
  you serve both apex and `www`, set
  `BETTER_AUTH_TRUSTED_ORIGINS=https://www.agentmesh.world,https://agentmesh.world`.

| Section | Path | What it does |
| --- | --- | --- |
| Overview | `/admin` | KPIs, sparklines, activity, system status |
| Pages & Content | `/admin/content` | Edit hero/CTA copy |
| Documentation | `/admin/docs` | Write/publish docs (Markdown + SEO) |
| Media | `/admin/media` | Upload, copy URL, delete (S3/R2) |
| Subscribers | `/admin/subscribers` | View + **export CSV** |
| Messages | `/admin/messages` | View + **export CSV** |
| Network Stats | `/admin/stats` | Edit live stats |
| Analytics | `/admin/analytics` | Lead conversion and tracking setup |
| Sales | `/admin/sales` | Payment gateway readiness + checkout attempts |
| Reports | `/admin/reports` | Launch readiness, sales, and setup checks |
| Users & Roles | `/admin/users` | Manage accounts and roles |
| Organization | `/admin/organization` | Manage admin organizations |
| Website settings | `/admin/settings` | Global site identity + default SEO |

## Payments

Xendit is the default checkout gateway. Stripe and Polar are configured as
fallback providers. Without provider credentials, `/api/checkout` redirects the
visitor to the contact form with a setup-required flag instead of breaking the
pricing page.

```env
PAYMENT_DEFAULT_PROVIDER="xendit"
XENDIT_SECRET_KEY="..."
STRIPE_SECRET_KEY="..."
POLAR_ACCESS_TOKEN="..."
POLAR_PRO_PRODUCT_ID="..."
```

Run `npm run db:migrate` after pulling this change so
`payment_transactions` exists before checkout/webhook traffic arrives.

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

## Analytics

Analytics is optional and disabled until provider env vars are configured.
The app tracks page views, CTA clicks, form starts, and successful/failed lead
forms without sending names, emails, company names, or message text.

```env
NEXT_PUBLIC_GA_MEASUREMENT_ID="G-..."
NEXT_PUBLIC_POSTHOG_KEY="phc_..."
NEXT_PUBLIC_POSTHOG_HOST="https://app.posthog.com"
```

See `../docs/20_ANALYTICS.md` for the measurement plan and validation checklist.
