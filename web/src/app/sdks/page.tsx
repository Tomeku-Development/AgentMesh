import type { Metadata } from "next";
import {
  PageHero,
  Section,
  SectionTitle,
  CtaBand,
} from "@/components/site/page-parts";
import { sdks } from "@/lib/content";
import { cn } from "@/lib/utils";

export const metadata: Metadata = {
  title: "SDKs — AgentMesh",
  description:
    "Client libraries for building with AgentMesh in TypeScript, Python, and on Casper.",
};

const statusColor: Record<(typeof sdks)[number]["status"], string> = {
  Stable: "bg-success/15 text-success",
  Beta: "bg-brand/15 text-brand",
  Planned: "bg-secondary text-muted-foreground",
};

export default function SdksPage() {
  return (
    <>
      <PageHero
        eyebrow="Developers"
        title="SDKs for your stack"
        description="Build agents and orchestrate organizations from the language you already use."
      />

      <Section>
        <SectionTitle eyebrow="Libraries" title="Official client SDKs" />
        <div className="mt-10 grid grid-cols-1 gap-6 lg:grid-cols-3">
          {sdks.map((sdk) => (
            <div
              key={sdk.name}
              className="flex flex-col rounded-xl border border-border bg-card p-6"
            >
              <div className="flex items-center justify-between">
                <h3 className="font-heading text-base font-semibold text-foreground">
                  {sdk.name}
                </h3>
                <span
                  className={cn(
                    "rounded-full px-2.5 py-1 text-[10px] font-semibold uppercase tracking-wider",
                    statusColor[sdk.status],
                  )}
                >
                  {sdk.status}
                </span>
              </div>
              <p className="mt-1 text-sm text-muted-foreground">
                {sdk.language}
              </p>
              <div className="mt-5 overflow-x-auto rounded-lg border border-border bg-background/60 p-3">
                <code className="font-mono text-xs text-foreground">
                  {sdk.install}
                </code>
              </div>
            </div>
          ))}
        </div>
      </Section>

      <CtaBand
        title="Start building"
        description="Read the quickstart and API reference to ship your first workflow."
        primary={{ label: "Documentation", href: "/docs" }}
        secondary={{ label: "API Reference", href: "/docs/api" }}
      />
    </>
  );
}
