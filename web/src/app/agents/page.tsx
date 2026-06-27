import type { Metadata } from "next";
import {
  PageHero,
  Section,
  SectionTitle,
  CtaBand,
} from "@/components/site/page-parts";
import { agentRoster } from "@/lib/content";

export const metadata: Metadata = {
  title: "Agents — AgentMesh",
  description:
    "Meet the specialized agents — Coordinator, Research, Finance, Legal, Risk, Treasury, Audit, and Execution — that make up an AgentMesh organization.",
};

export default function AgentsPage() {
  return (
    <>
      <PageHero
        eyebrow="Agents"
        title="A team of specialists, not one generalist"
        description="Every agent owns a single responsibility and carries its own memory, tools, permissions, and wallet. Together they form an autonomous organization."
      />

      <Section>
        <SectionTitle
          eyebrow="The roster"
          title="Specialized roles that collaborate"
        />
        <div className="mt-12 grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
          {agentRoster.map((agent) => {
            const Icon = agent.icon;
            return (
              <div
                key={agent.name}
                className="group flex flex-col rounded-xl border border-border bg-card p-6 transition-colors duration-200 hover:bg-secondary/50"
              >
                <div className="flex items-center justify-between">
                  <Icon
                    className="size-7 text-brand transition-transform duration-200 group-hover:scale-110"
                    strokeWidth={1.5}
                    aria-hidden
                  />
                  <span className="rounded-full bg-brand/10 px-2.5 py-1 text-[10px] font-semibold uppercase tracking-wider text-brand">
                    {agent.role}
                  </span>
                </div>
                <h3 className="mt-4 font-heading text-base font-semibold text-foreground">
                  {agent.name}
                </h3>
                <ul className="mt-3 space-y-1.5">
                  {agent.responsibilities.map((r) => (
                    <li
                      key={r}
                      className="text-xs leading-relaxed text-muted-foreground"
                    >
                      • {r}
                    </li>
                  ))}
                </ul>
              </div>
            );
          })}
        </div>
      </Section>

      <CtaBand
        title="Bring your own agents"
        description="The agent SDK lets you publish and install custom agents. A marketplace is on the roadmap."
        primary={{ label: "Explore SDKs", href: "/sdks" }}
        secondary={{ label: "Read the docs", href: "/docs" }}
      />
    </>
  );
}
