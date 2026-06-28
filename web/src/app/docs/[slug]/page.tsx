import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import {
  getDocBySlug,
  getPublishedDocs,
  groupByCategory,
  renderMarkdown,
} from "@/lib/data/docs";
import { cn } from "@/lib/utils";

export const dynamic = "force-dynamic";

export async function generateMetadata({
  params,
}: {
  params: Promise<{ slug: string }>;
}): Promise<Metadata> {
  const { slug } = await params;
  const doc = await getDocBySlug(slug);
  if (!doc || !doc.published) return { title: "Not found — AgentMesh" };
  return {
    title: `${doc.seoTitle || doc.title} — AgentMesh Docs`,
    description: doc.seoDescription || doc.summary || undefined,
  };
}

export default async function DocPage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;
  const [doc, allDocs] = await Promise.all([
    getDocBySlug(slug),
    getPublishedDocs(),
  ]);

  if (!doc || !doc.published) notFound();

  const groups = groupByCategory(allDocs);
  const html = renderMarkdown(doc.body);

  return (
    <div className="mx-auto max-w-7xl px-5 pt-28 sm:px-8 sm:pt-32">
      <div className="grid grid-cols-1 gap-10 lg:grid-cols-[240px_1fr]">
        {/* Sidebar */}
        <aside className="lg:sticky lg:top-24 lg:h-fit">
          <Link
            href="/docs"
            className="text-xs font-semibold uppercase tracking-wider text-brand hover:underline"
          >
            ← All docs
          </Link>
          <nav className="mt-5 flex flex-col gap-6">
            {groups.map((group) => (
              <div key={group.category}>
                <p className="mb-2 text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
                  {group.category}
                </p>
                <ul className="flex flex-col gap-0.5 border-l border-border">
                  {group.docs.map((d) => {
                    const active = d.slug === doc.slug;
                    return (
                      <li key={d.id}>
                        <Link
                          href={`/docs/${d.slug}`}
                          className={cn(
                            "-ml-px block border-l-2 py-1.5 pl-4 text-sm transition-colors",
                            active
                              ? "border-brand font-medium text-brand"
                              : "border-transparent text-muted-foreground hover:border-border hover:text-foreground",
                          )}
                        >
                          {d.title}
                        </Link>
                      </li>
                    );
                  })}
                </ul>
              </div>
            ))}
          </nav>
        </aside>

        {/* Content */}
        <article className="min-w-0 pb-20">
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-brand">
            {doc.category}
          </p>
          <h1 className="mt-3 font-heading text-3xl font-bold tracking-tight text-foreground sm:text-4xl">
            {doc.title}
          </h1>
          {doc.summary && (
            <p className="mt-3 text-base leading-relaxed text-muted-foreground">
              {doc.summary}
            </p>
          )}
          <hr className="my-8 border-border" />
          <div
            className={cn(
              "max-w-none text-sm leading-relaxed text-muted-foreground",
              "[&_h2]:mt-10 [&_h2]:font-heading [&_h2]:text-xl [&_h2]:font-semibold [&_h2]:text-foreground",
              "[&_h3]:mt-7 [&_h3]:font-heading [&_h3]:text-base [&_h3]:font-semibold [&_h3]:text-foreground",
              "[&_p]:mt-4 [&_p]:leading-relaxed",
              "[&_a]:text-brand [&_a]:underline-offset-4 hover:[&_a]:underline",
              "[&_ul]:mt-4 [&_ul]:list-disc [&_ul]:pl-6 [&_ol]:mt-4 [&_ol]:list-decimal [&_ol]:pl-6 [&_li]:mt-1.5",
              "[&_code]:rounded [&_code]:bg-secondary [&_code]:px-1.5 [&_code]:py-0.5 [&_code]:font-mono [&_code]:text-[0.85em] [&_code]:text-foreground",
              "[&_pre]:mt-4 [&_pre]:overflow-x-auto [&_pre]:rounded-xl [&_pre]:border [&_pre]:border-border [&_pre]:bg-card [&_pre]:p-4 [&_pre_code]:bg-transparent [&_pre_code]:p-0",
              "[&_blockquote]:mt-4 [&_blockquote]:border-l-2 [&_blockquote]:border-brand/50 [&_blockquote]:pl-4 [&_blockquote]:italic",
              "[&_strong]:text-foreground [&_h1]:font-heading [&_h1]:text-2xl [&_h1]:font-bold [&_h1]:text-foreground [&_h1]:mt-8",
              "[&_table]:mt-4 [&_table]:w-full [&_th]:border [&_th]:border-border [&_th]:bg-secondary [&_th]:px-3 [&_th]:py-2 [&_th]:text-left [&_th]:text-foreground [&_td]:border [&_td]:border-border [&_td]:px-3 [&_td]:py-2",
              "[&_img]:mt-4 [&_img]:rounded-xl [&_img]:border [&_img]:border-border",
            )}
            // Sanitized HTML generated from Markdown.
            dangerouslySetInnerHTML={{ __html: html }}
          />
        </article>
      </div>
    </div>
  );
}
