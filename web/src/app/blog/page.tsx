import type { Metadata } from "next";
import Link from "next/link";
import { ArrowRight } from "lucide-react";
import { PageHero, Section } from "@/components/site/page-parts";
import { blogPosts } from "@/lib/content";

export const metadata: Metadata = {
  title: "Blog — AgentMesh",
  description:
    "Product news, engineering deep-dives, and writing on the future of autonomous organizations.",
};

const dateFmt = new Intl.DateTimeFormat("en-US", {
  year: "numeric",
  month: "short",
  day: "numeric",
});

export default function BlogPage() {
  return (
    <>
      <PageHero
        eyebrow="Company"
        title="Blog"
        description="Product news, engineering deep-dives, and our perspective on the agent economy."
      />

      <Section>
        <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3">
          {blogPosts.map((post) => (
            <Link
              key={post.slug}
              href={`/blog/${post.slug}`}
              className="group flex flex-col rounded-xl border border-border bg-card p-6 transition-colors duration-200 hover:bg-secondary/50"
            >
              <div className="flex items-center gap-3 text-xs text-muted-foreground">
                <span className="rounded-full bg-brand/10 px-2.5 py-1 font-semibold uppercase tracking-wider text-brand">
                  {post.category}
                </span>
                <span>{post.readingTime}</span>
              </div>
              <h3 className="mt-4 flex-1 font-heading text-lg font-semibold leading-snug text-foreground">
                {post.title}
              </h3>
              <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
                {post.excerpt}
              </p>
              <div className="mt-5 flex items-center justify-between">
                <time className="text-xs text-muted-foreground" dateTime={post.date}>
                  {dateFmt.format(new Date(post.date))}
                </time>
                <ArrowRight className="size-4 text-brand transition-transform group-hover:translate-x-0.5" />
              </div>
            </Link>
          ))}
        </div>
      </Section>
    </>
  );
}
