import type { Metadata } from "next";
import Link from "next/link";
import { ArrowUpRight, MapPin } from "lucide-react";
import {
  PageHero,
  Section,
  SectionTitle,
  IconGrid,
} from "@/components/site/page-parts";
import { jobOpenings, companyValues } from "@/lib/content";

export const metadata: Metadata = {
  title: "Careers — AgentMesh",
  description:
    "Help build the operating system for autonomous organizations. Remote-first roles across platform, agents, protocol, and design.",
};

export default function CareersPage() {
  return (
    <>
      <PageHero
        eyebrow="Company"
        title="Build the future of autonomous organizations"
        description="We're a remote-first team shipping infrastructure where AI agents collaborate and execute with verifiable trust. Come build it with us."
      />

      <Section>
        <SectionTitle eyebrow="Open roles" title="Where you can help" />
        <div className="mt-10 overflow-hidden rounded-xl border border-border">
          {jobOpenings.map((job, i) => (
            <Link
              key={job.title}
              href="/contact"
              className={`group flex flex-col gap-2 bg-card p-5 transition-colors hover:bg-secondary/50 sm:flex-row sm:items-center sm:justify-between ${
                i !== 0 ? "border-t border-border" : ""
              }`}
            >
              <div>
                <h3 className="font-heading text-base font-semibold text-foreground">
                  {job.title}
                </h3>
                <p className="mt-1 text-sm text-muted-foreground">{job.team}</p>
              </div>
              <div className="flex items-center gap-5 text-sm text-muted-foreground">
                <span className="inline-flex items-center gap-1.5">
                  <MapPin className="size-4" />
                  {job.location}
                </span>
                <span>{job.type}</span>
                <ArrowUpRight className="size-4 text-brand transition-transform group-hover:translate-x-0.5 group-hover:-translate-y-0.5" />
              </div>
            </Link>
          ))}
        </div>
        <p className="mt-4 text-sm text-muted-foreground">
          Don&apos;t see your role?{" "}
          <Link
            href="/contact"
            className="text-brand underline-offset-4 hover:underline"
          >
            Reach out anyway
          </Link>
          .
        </p>
      </Section>

      <Section className="border-t border-border bg-secondary/20">
        <SectionTitle eyebrow="How we work" title="Our values" />
        <div className="mt-10">
          <IconGrid items={companyValues} columns={3} />
        </div>
      </Section>
    </>
  );
}
