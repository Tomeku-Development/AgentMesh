import type { Metadata } from "next";
import {
  PageHero,
  Section,
  SectionTitle,
  IconGrid,
  CtaBand,
} from "@/components/site/page-parts";
import { companyValues } from "@/lib/content";

export const metadata: Metadata = {
  title: "About — AgentMesh",
  description:
    "AgentMesh is building the operating system for autonomous organizations — by Tomeku, for the Casper ecosystem.",
};

export default function AboutPage() {
  return (
    <>
      <PageHero
        eyebrow="Company"
        title="We believe the future of organizations is autonomous"
        description="Software should no longer simply assist people. It should reason, collaborate, negotiate, execute, and verify. AgentMesh is the infrastructure for that future."
      />

      <Section>
        <div className="grid grid-cols-1 gap-12 lg:grid-cols-2">
          <div>
            <SectionTitle eyebrow="Mission" title="Infrastructure for autonomous organizations" />
            <p className="mt-5 text-sm leading-relaxed text-muted-foreground">
              We combine multi-agent AI, blockchain, verifiable execution, and
              transparent governance to turn isolated AI assistants into
              collaborative digital organizations capable of making trustworthy
              decisions.
            </p>
          </div>
          <div>
            <SectionTitle eyebrow="Vision" title="Software that runs the work" />
            <p className="mt-5 text-sm leading-relaxed text-muted-foreground">
              Organizations succeed because specialists collaborate. AgentMesh
              brings that model to AI — anchored in verifiable trust on Casper —
              so teams can delegate not just analysis, but trusted action.
            </p>
          </div>
        </div>
      </Section>

      <Section className="border-t border-border bg-secondary/20">
        <SectionTitle eyebrow="Values" title="What we optimize for" />
        <div className="mt-10">
          <IconGrid items={companyValues} columns={3} />
        </div>
      </Section>

      <Section>
        <div className="rounded-2xl border border-border bg-card p-8 text-center">
          <p className="text-sm uppercase tracking-[0.2em] text-muted-foreground">
            Built by
          </p>
          <p className="mt-3 font-heading text-2xl font-bold text-foreground">
            Tomeku
          </p>
          <p className="mt-2 text-sm text-muted-foreground">
            Built for the Casper Agentic Buildathon.{" "}
            <a
              href="https://tomeku.com"
              target="_blank"
              rel="noopener noreferrer"
              className="text-brand underline-offset-4 hover:underline"
            >
              tomeku.com
            </a>
          </p>
        </div>
      </Section>

      <CtaBand
        title="Join us"
        description="We're hiring builders who want to ship the operating system for autonomous organizations."
        primary={{ label: "See open roles", href: "/careers" }}
        secondary={{ label: "Get in touch", href: "/contact" }}
      />
    </>
  );
}
