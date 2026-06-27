// Seed a few starter documentation pages. Idempotent (ON CONFLICT DO NOTHING).
// Run: node --env-file=.env.local scripts/seed-docs.mjs
import postgres from "postgres";

const sql = postgres(process.env.DATABASE_URL);

const docs = [
  {
    slug: "getting-started",
    title: "Getting Started",
    category: "Introduction",
    summary: "Create your first autonomous organization and run a workflow.",
    sort_order: 1,
    published: true,
    body: `# Getting Started

AgentMesh lets you build **autonomous organizations** — teams of specialized AI agents that collaborate, reach consensus, and execute trusted actions on Casper.

## Install the SDK

\`\`\`bash
npm install @agentmesh/sdk
\`\`\`

## Run your first workflow

\`\`\`ts
import { AgentMesh } from "@agentmesh/sdk";

const mesh = new AgentMesh({ apiKey: process.env.AGENTMESH_API_KEY });
const run = await mesh.organizations("invest-committee").submit({
  goal: "Evaluate the attached startup for a seed investment.",
});

console.log(run.decision, run.casperTxHash);
\`\`\`

Every decision is recorded on-chain for full transparency.`,
  },
  {
    slug: "core-concepts",
    title: "Core Concepts",
    category: "Introduction",
    summary: "Agents, the mesh, consensus, and on-chain execution.",
    sort_order: 2,
    published: true,
    body: `# Core Concepts

## Agents

Each agent owns a single responsibility and carries its own memory, tools, permissions, and wallet.

## The Mesh

A coordinator routes a goal to the right specialists, who analyze in parallel.

## Consensus

Agents debate and vote. A consensus engine produces an explainable recommendation with a confidence score.

## On-Chain Trust

Approved actions execute through Casper smart contracts, producing an immutable audit trail.`,
  },
  {
    slug: "on-chain-trust",
    title: "On-Chain Trust",
    category: "Platform",
    summary: "How decisions become verifiable, permanent records on Casper.",
    sort_order: 1,
    published: true,
    body: `# On-Chain Trust

AgentMesh separates **off-chain reasoning** (fast, private) from **on-chain trust** (permanent, verifiable).

- Proposals, votes, and outcomes are written to Casper.
- Anyone can verify what was decided, by whom, and why.
- Agent wallets enforce spending limits, and critical actions require human approval.

> Off-chain reasoning. On-chain trust.`,
  },
];

for (const d of docs) {
  await sql`
    insert into doc_pages (slug, title, category, summary, body, sort_order, published)
    values (${d.slug}, ${d.title}, ${d.category}, ${d.summary}, ${d.body}, ${d.sort_order}, ${d.published})
    on conflict (slug) do nothing
  `;
}

const [{ count }] = await sql`select count(*)::int as count from doc_pages`;
console.log("doc_pages total:", count);
await sql.end();
