import type { Metadata } from "next";
import {
  PageHero,
  Section,
  SectionTitle,
  CtaBand,
} from "@/components/site/page-parts";
import { AgentNetwork } from "@/components/site/agent-network";
import { steps } from "@/lib/content";

export const metadata: Metadata = {
  title: "Multi-Agent Mesh — AgentMesh",
  description:
    "Specialized AI agents collaborate as a coordinated mesh — analyzing, debating, and reaching consensus before any action executes.",
};

export default function MultiAgentMeshPage() {
  return (
    <>
      <PageHero
        eyebrow="Platform"
        title="A coordinated mesh of specialized agents"
        description="Instead of one generalist assistant, AgentMesh runs a team of specialists — each with its own memory, tools, permissions, and wallet — that collaborate toward a shared goal."
      />

      <Section>
        <div className="grid grid-cols-1 items-center gap-14 lg:grid-cols-2">
          <div>
            <SectionTitle
              eyebrow="How consensus works"
              title="Analyze, debate, decide"
              description="The coordinator routes your goal to the right specialists. They contribute evidence in parallel, a consensus engine resolves conflicts, and only then is an action proposed."
            />
            <ol className="mt-8 space-y-6">
              {steps.map((step) => (
                <li key={step.number} className="flex gap-4">
                  <span className="mt-0.5 font-mono text-base font-bold tabular-nums text-brand">
                    {step.number}
                  </span>
                  <div>
                    <h3 className="font-heading text-base font-semibold text-foreground">
                      {step.title}
                    </h3>
                    <p className="mt-1 max-w-sm text-sm leading-relaxed text-muted-foreground">
                      {step.description}
                    </p>
                  </div>
                </li>
              ))}
            </ol>
          </div>

          <div>
            <AgentNetwork />
            <p className="mt-6 text-center text-xs font-semibold uppercase tracking-[0.35em] text-brand/80">
              Casper Network
            </p>
          </div>
        </div>
      </Section>

      <Section className="border-t border-border bg-secondary/20">
        <SectionTitle
          eyebrow="Why a mesh"
          title="Specialists outperform generalists"
          description="Real organizations succeed because experts collaborate. AgentMesh brings that structure to AI."
        />
        <div className="mt-10 grid grid-cols-1 gap-px overflow-hidden rounded-xl border border-border bg-border sm:grid-cols-3">
          {[
            {
              k: "Transparent reasoning",
              v: "Every recommendation carries supporting evidence — no black boxes.",
            },
            {
              k: "Collaborative decisions",
              v: "Agents debate and vote before consensus is reached.",
            },
            {
              k: "Observable & governable",
              v: "Agents communicate through the orchestrator, so every run is traceable.",
            },
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
        title="Trust, anchored on Casper"
        description="See how decisions become permanent, verifiable on-chain records."
        primary={{ label: "On-Chain Trust", href: "/platform/on-chain-trust" }}
        secondary={{ label: "Meet the agents", href: "/agents" }}
      />
    </>
  );
}
