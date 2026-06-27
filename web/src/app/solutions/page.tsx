import type { Metadata } from "next";
import {
  PageHero,
  Section,
  IconGrid,
  CtaBand,
} from "@/components/site/page-parts";
import { solutions } from "@/lib/content";

export const metadata: Metadata = {
  title: "Solutions — AgentMesh",
  description:
    "Autonomous workflows for venture due diligence, treasury management, DAO governance, compliance, RWA verification, and procurement.",
};

export default function SolutionsPage() {
  return (
    <>
      <PageHero
        eyebrow="Solutions"
        title="Autonomous workflows for real organizations"
        description="AgentMesh shines on trust-sensitive work — where decisions need evidence, collaboration, and a verifiable record."
      />

      <Section>
        <IconGrid items={solutions} columns={3} />
      </Section>

      <CtaBand
        title="Have a workflow in mind?"
        description="Tell us what you're automating and we'll help you design the agent organization for it."
        primary={{ label: "Talk to us", href: "/contact" }}
        secondary={{ label: "Explore the platform", href: "/platform" }}
      />
    </>
  );
}
