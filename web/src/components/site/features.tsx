import Link from "next/link";
import { ArrowUpRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import { features } from "@/lib/content";

export function Features() {
  return (
    <section id="platform" className="relative py-24 sm:py-28">
      <div className="mx-auto max-w-7xl px-5 sm:px-8">
        <p className="flex items-center gap-3 text-xs font-medium uppercase tracking-[0.25em] text-brand">
          <span className="h-px w-6 bg-brand" />
          Built for the Future
        </p>

        <div className="mt-6 flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
          <h2 className="max-w-md font-heading text-3xl font-bold leading-tight tracking-tight text-foreground sm:text-4xl">
            The Power of a<br />
            Multi-Agent Network
          </h2>
          <div className="flex max-w-md flex-col items-start gap-5 lg:items-end">
            <p className="text-sm leading-relaxed text-muted-foreground lg:text-right">
              Specialized AI agents work together as a coordinated mesh to
              analyze, decide, and execute complex tasks with transparency and
              trust.
            </p>
            <Button
              asChild
              variant="outline"
              className="rounded-md border-border bg-transparent"
            >
              <Link href="#solutions">
                Explore Platform
                <ArrowUpRight className="size-4" />
              </Link>
            </Button>
          </div>
        </div>

        <div className="mt-14 grid grid-cols-1 gap-px overflow-hidden rounded-xl border border-border bg-border sm:grid-cols-2 lg:grid-cols-5">
          {features.map((feature) => {
            const Icon = feature.icon;
            return (
              <div
                key={feature.title}
                className="group relative flex flex-col gap-5 bg-card p-6 transition-colors duration-200 hover:bg-secondary/50"
              >
                <Icon
                  className="size-8 text-brand transition-transform duration-200 group-hover:scale-110"
                  strokeWidth={1.5}
                  aria-hidden
                />
                <div className="flex flex-col gap-2">
                  <h3 className="font-heading text-base font-semibold leading-snug text-foreground">
                    {feature.title}
                  </h3>
                  <p className="text-sm leading-relaxed text-muted-foreground">
                    {feature.description}
                  </p>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
