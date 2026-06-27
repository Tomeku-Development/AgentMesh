import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { ArrowLeft } from "lucide-react";
import { Prose } from "@/components/site/page-parts";
import { blogPosts } from "@/lib/content";

const dateFmt = new Intl.DateTimeFormat("en-US", {
  year: "numeric",
  month: "long",
  day: "numeric",
});

export function generateStaticParams() {
  return blogPosts.map((p) => ({ slug: p.slug }));
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ slug: string }>;
}): Promise<Metadata> {
  const { slug } = await params;
  const post = blogPosts.find((p) => p.slug === slug);
  if (!post) return { title: "Not found — AgentMesh" };
  return { title: `${post.title} — AgentMesh`, description: post.excerpt };
}

export default async function BlogPostPage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;
  const post = blogPosts.find((p) => p.slug === slug);
  if (!post) notFound();

  return (
    <article>
      <div className="border-b border-border">
        <div className="mx-auto max-w-3xl px-5 pb-12 pt-32 sm:px-8 sm:pt-36">
          <Link
            href="/blog"
            className="inline-flex items-center gap-1.5 text-sm text-muted-foreground transition-colors hover:text-foreground"
          >
            <ArrowLeft className="size-4" />
            Back to blog
          </Link>
          <div className="mt-6 flex items-center gap-3 text-xs text-muted-foreground">
            <span className="rounded-full bg-brand/10 px-2.5 py-1 font-semibold uppercase tracking-wider text-brand">
              {post.category}
            </span>
            <time dateTime={post.date}>{dateFmt.format(new Date(post.date))}</time>
            <span>· {post.readingTime}</span>
          </div>
          <h1 className="mt-5 font-heading text-3xl font-bold leading-tight tracking-tight text-foreground sm:text-4xl">
            {post.title}
          </h1>
        </div>
      </div>

      <Prose>
        <p className="text-base text-foreground">{post.excerpt}</p>
        <p>
          This article is part of the AgentMesh blog. The full write-up is coming
          soon — in the meantime, explore the platform to see how a mesh of
          specialized agents collaborates, reaches consensus, and executes
          verifiable actions on Casper.
        </p>
        <h2>Why it matters</h2>
        <p>
          AgentMesh separates fast, private off-chain reasoning from permanent,
          verifiable on-chain trust. That combination is what makes autonomous
          organizations practical for real, trust-sensitive work.
        </p>
        <ul>
          <li>Specialized agents with memory, tools, permissions, and wallets.</li>
          <li>A consensus engine that produces explainable decisions.</li>
          <li>Immutable audit trails recorded on the Casper Network.</li>
        </ul>
        <p>
          Want to go deeper?{" "}
          <Link href="/platform">Explore the platform</Link> or{" "}
          <Link href="/contact">get in touch</Link>.
        </p>
      </Prose>
    </article>
  );
}
