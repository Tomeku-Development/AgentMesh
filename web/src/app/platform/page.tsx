import type { Metadata } from "next";
import {
  PageHero,
  Section,
  SectionTitle,
  IconGrid,
  CtaBand,
} from "@/components/site/page-parts";
import { features } from "@/lib/content";

export const metadata: Metadata = {
  title: "Platform Overview — AgentMesh",
  description:
    "How the AgentMesh platform turns specialized AI agents into autonomous organizations with verifiable on-chain execution on Casper.",
};

const layers = [
  {
    title: "Experience Layer",
    body: "A control-room dashboard and website where you create organizations, submit goals, and watch agents work in real time.",
  },
  {
    title: "Orchestration Layer",
    body: "A LangGraph workflow engine routes goals to specialists, manages state, and drives the consensus process.",
  },
  {
    title: "Agent Layer",
    body: "Specialized agents — each with memory, tools, permissions, and a wallet — analyze, debate, and decide.",
  },
  {
    title: "Trust Layer",
    body: "Casper smart contracts record proposals, votes, and treasury actions as an immutable, verifiable audit trail.",
  },
];

export default function PlatformPage() {
  return (
    <>
      <PageHero
        eyebrow="Platform"
        title="The operating system for autonomous organizations"
        description="AgentMesh coordinates specialized AI agents into a digital organization that reasons, reaches consensus, and executes trusted actions on Casper."
      />

      <Section>
        <SectionTitle
          eyebrow="Architecture"
          title="Four layers, one trusted system"
          description="Each layer has a clear responsibility — from the interface you use to the chain that guarantees trust."
        />
        <div className="mt-12 grid grid-cols-1 gap-px overflow-hidden rounded-xl border border-border bg-border md:grid-cols-2">
          {layers.map((layer, i) => (
            <div key={layer.title} className="bg-card p-7">
              <span className="font-mono text-sm font-bold text-brand">
                0{i + 1}
              </span>
              <h3 className="mt-3 font-heading text-lg font-semibold text-foreground">
                {layer.title}
              </h3>
              <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
                {layer.body}
              </p>
            </div>
          ))}
        </div>
      </Section>

      <Section className="border-t border-border bg-secondary/20">
        <SectionTitle
          eyebrow="Capabilities"
          title="Everything you need to run autonomous workflows"
        />
        <div className="mt-12">
          <IconGrid items={features} columns={3} />
        </div>
      </Section>

      <CtaBand
        title="See the platform in action"
        description="Explore how the multi-agent mesh reaches consensus and how every decision is anchored on Casper."
        primary={{ label: "Multi-Agent Mesh", href: "/platform/multi-agent-mesh" }}
        secondary={{ label: "On-Chain Trust", href: "/platform/on-chain-trust" }}
      />
    </>
  );
}
