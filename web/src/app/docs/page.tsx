import type { Metadata } from "next";
import Link from "next/link";
import { ArrowRight, FileText } from "lucide-react";
import {
  PageHero,
  Section,
  SectionTitle,
  CtaBand,
} from "@/components/site/page-parts";
import { docSections, GITHUB_URL } from "@/lib/content";
import { getPublishedDocs, groupByCategory } from "@/lib/data/docs";

export const metadata: Metadata = {
  title: "Documentation — AgentMesh",
  description:
    "Guides, concepts, and references for building autonomous organizations with AgentMesh on Casper.",
};

export const dynamic = "force-dynamic";

export default async function DocsPage() {
  const docs = await getPublishedDocs();
  const groups = groupByCategory(docs);

  return (
    <>
      <PageHero
        eyebrow="Developers"
        title="Documentation"
        description="Everything you need to build, orchestrate, and deploy multi-agent organizations on Casper."
      />

      <Section>
        {groups.length > 0 ? (
          <div className="flex flex-col gap-10">
            {groups.map((group) => (
              <div key={group.category}>
                <SectionTitle title={group.category} />
                <div className="mt-6 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
                  {group.docs.map((doc) => (
                    <Link
                      key={doc.id}
                      href={`/docs/${doc.slug}`}
                      className="group flex flex-col rounded-xl border border-border bg-card p-5 transition-colors hover:bg-secondary/50"
                    >
                      <FileText className="size-5 text-brand" />
                      <h3 className="mt-3 flex items-center gap-1.5 font-heading text-base font-semibold text-foreground">
                        {doc.title}
                        <ArrowRight className="size-4 text-muted-foreground transition-transform group-hover:translate-x-0.5" />
                      </h3>
                      {doc.summary && (
                        <p className="mt-1.5 text-sm leading-relaxed text-muted-foreground">
                          {doc.summary}
                        </p>
                      )}
                    </Link>
                  ))}
                </div>
              </div>
            ))}
            <div>
              <Link
                href="/docs/api"
                className="inline-flex items-center gap-1.5 text-sm text-brand hover:underline"
              >
                API Reference
                <ArrowRight className="size-4" />
              </Link>
            </div>
          </div>
        ) : (
          // Fallback when no docs have been published yet.
          <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
            {docSections.map((doc) => {
              const Icon = doc.icon;
              return (
                <Link
                  key={doc.title}
                  href={doc.href}
                  className="group flex items-start gap-4 rounded-xl border border-border bg-card p-6 transition-colors hover:bg-secondary/50"
                >
                  <Icon className="mt-0.5 size-6 shrink-0 text-brand" strokeWidth={1.5} />
                  <div>
                    <h3 className="font-heading text-base font-semibold text-foreground">
                      {doc.title}
                    </h3>
                    <p className="mt-1.5 text-sm leading-relaxed text-muted-foreground">
                      {doc.description}
                    </p>
                  </div>
                </Link>
              );
            })}
          </div>
        )}
      </Section>

      <CtaBand
        title="Dive into the API"
        description="Browse endpoints, payloads, and authentication, or grab a client SDK."
        primary={{ label: "API Reference", href: "/docs/api" }}
        secondary={{ label: "View on GitHub", href: GITHUB_URL }}
      />
    </>
  );
}
