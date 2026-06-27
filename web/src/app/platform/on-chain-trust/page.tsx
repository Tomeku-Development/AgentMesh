import type { Metadata } from "next";
import {
  PageHero,
  Section,
  SectionTitle,
  IconGrid,
  CtaBand,
} from "@/components/site/page-parts";
import { ShieldCheck, FileSearch, Lock, Coins } from "lucide-react";

export const metadata: Metadata = {
  title: "On-Chain Trust — AgentMesh",
  description:
    "AgentMesh separates off-chain reasoning from on-chain trust. Every critical decision is recorded on Casper as an immutable, verifiable audit trail.",
};

const pillars = [
  {
    icon: ShieldCheck,
    title: "Verifiable Decisions",
    description:
      "Proposals, votes, and outcomes are written to Casper smart contracts — provable by anyone.",
  },
  {
    icon: FileSearch,
    title: "Immutable Audit Trail",
    description:
      "Reconstruct what was decided, who authorized it, and which evidence influenced it.",
  },
  {
    icon: Lock,
    title: "Policy-Bound Execution",
    description:
      "Agent wallets enforce spending limits on- and off-chain. Critical actions need human approval.",
  },
  {
    icon: Coins,
    title: "Agent Economy Ready",
    description:
      "x402 payments and MCP tooling let agents transact and settle on Casper.",
  },
];

export default function OnChainTrustPage() {
  return (
    <>
      <PageHero
        eyebrow="Platform"
        title="Off-chain reasoning. On-chain trust."
        description="Agents reason fast and privately off-chain. The decision, its inputs, and its authorization are recorded permanently on Casper — so any third party can verify them without trusting the operator."
      />

      <Section>
        <IconGrid items={pillars} columns={2} />
      </Section>

      <Section className="border-t border-border bg-secondary/20">
        <SectionTitle
          eyebrow="The flow"
          title="From reasoning to verifiable record"
        />
        <div className="mt-10 overflow-x-auto rounded-xl border border-border bg-card p-6">
          <pre className="font-mono text-xs leading-relaxed text-muted-foreground sm:text-sm">
{`  Goal
   │
   ▼
 Specialist agents  ──►  evidence + positions      (off-chain)
   │
   ▼
 Consensus engine   ──►  recommendation + score    (off-chain)
   │
   ▼
 Human approval     ──►  authorize critical action
   │
   ▼
 Casper contract    ──►  proposal · vote · execution (on-chain)
   │
   ▼
 Immutable audit trail  ──►  verify anytime, by anyone`}
          </pre>
        </div>
      </Section>

      <Section>
        <div className="grid grid-cols-1 gap-px overflow-hidden rounded-xl border border-border bg-border sm:grid-cols-3">
          {[
            { k: "Casper Network", v: "Predictable fees for frequent agent actions." },
            { k: "Odra Contracts", v: "Upgradeable contracts that evolve without losing state." },
            { k: "CSPR.cloud", v: "Reliable RPC access for deploys and reads." },
          ].map((item) => (
            <div key={item.k} className="bg-card p-6">
              <h3 className="font-heading text-base font-semibold text-foreground">
                {item.k}
              </h3>
              <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
                {item.v}
              </p>
            </div>
          ))}
        </div>
      </Section>

      <CtaBand
        title="Build with verifiable trust"
        description="Start on Casper Testnet today, or talk to us about enterprise deployment."
        primary={{ label: "View pricing", href: "/pricing" }}
        secondary={{ label: "Read the docs", href: "/docs" }}
      />
    </>
  );
}
