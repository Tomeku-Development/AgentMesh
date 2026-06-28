import Link from "next/link";
import { ArrowRight, type LucideIcon } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

/**
 * Page hero used at the top of every content page. Includes top padding to
 * clear the fixed navbar.
 */
export function PageHero({
  eyebrow,
  title,
  description,
  children,
}: {
  eyebrow?: string;
  title: string;
  description?: string;
  children?: React.ReactNode;
}) {
  return (
    <section className="relative overflow-hidden border-b border-border">
      <div className="pointer-events-none absolute -top-40 left-1/2 -z-10 size-[500px] -translate-x-1/2 brand-glow opacity-40" />
      <div className="mx-auto max-w-7xl px-5 pb-14 pt-32 sm:px-8 sm:pt-36">
        {eyebrow && (
          <p className="flex items-center gap-3 text-xs font-medium uppercase tracking-[0.25em] text-brand">
            <span className="h-px w-6 bg-brand" />
            {eyebrow}
          </p>
        )}
        <h1 className="mt-5 max-w-3xl font-heading text-4xl font-bold leading-tight tracking-tight text-foreground sm:text-5xl">
          {title}
        </h1>
        {description && (
          <p className="mt-5 max-w-2xl text-base leading-relaxed text-muted-foreground sm:text-lg">
            {description}
          </p>
        )}
        {children && <div className="mt-8">{children}</div>}
      </div>
    </section>
  );
}

export function Section({
  children,
  className,
  id,
}: {
  children: React.ReactNode;
  className?: string;
  id?: string;
}) {
  return (
    <section id={id} className={cn("py-16 sm:py-20", className)}>
      <div className="mx-auto max-w-7xl px-5 sm:px-8">{children}</div>
    </section>
  );
}

export function SectionTitle({
  eyebrow,
  title,
  description,
}: {
  eyebrow?: string;
  title: string;
  description?: string;
}) {
  return (
    <div className="max-w-2xl">
      {eyebrow && (
        <p className="flex items-center gap-3 text-xs font-medium uppercase tracking-[0.25em] text-brand">
          <span className="h-px w-6 bg-brand" />
          {eyebrow}
        </p>
      )}
      <h2 className="mt-5 font-heading text-2xl font-bold tracking-tight text-foreground sm:text-3xl">
        {title}
      </h2>
      {description && (
        <p className="mt-4 text-base leading-relaxed text-muted-foreground">
          {description}
        </p>
      )}
    </div>
  );
}

export type IconItem = {
  icon: LucideIcon;
  title: string;
  description: string;
};

export function IconGrid({
  items,
  columns = 3,
}: {
  items: IconItem[];
  columns?: 2 | 3;
}) {
  return (
    <div
      className={cn(
        "grid grid-cols-1 gap-5 sm:grid-cols-2",
        columns === 3 ? "lg:grid-cols-3" : "lg:grid-cols-2",
      )}
    >
      {items.map((item) => {
        const Icon = item.icon;
        return (
          <div
            key={item.title}
            className="group rounded-xl border border-border bg-card p-6 transition-colors duration-200 hover:bg-secondary/50"
          >
            <Icon
              className="size-7 text-brand transition-transform duration-200 group-hover:scale-110"
              strokeWidth={1.5}
              aria-hidden
            />
            <h3 className="mt-4 font-heading text-base font-semibold text-foreground">
              {item.title}
            </h3>
            <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
              {item.description}
            </p>
          </div>
        );
      })}
    </div>
  );
}

/** Bottom-of-page call to action band. */
export function CtaBand({
  title,
  description,
  primary,
  secondary,
}: {
  title: string;
  description?: string;
  primary: { label: string; href: string };
  secondary?: { label: string; href: string };
}) {
  return (
    <section className="relative overflow-hidden border-t border-border py-20 sm:py-24">
      <div className="pointer-events-none absolute left-1/2 top-1/2 -z-10 size-[500px] -translate-x-1/2 -translate-y-1/2 brand-glow opacity-50" />
      <div className="mx-auto max-w-3xl px-5 text-center sm:px-8">
        <h2 className="display-italic text-3xl leading-tight text-foreground sm:text-4xl">
          {title}
        </h2>
        {description && (
          <p className="mx-auto mt-5 max-w-xl text-base leading-relaxed text-muted-foreground">
            {description}
          </p>
        )}
        <div className="mt-8 flex flex-col items-center justify-center gap-3 sm:flex-row">
          <Button asChild size="lg" className="h-12 rounded-md px-6">
            <Link
              href={primary.href}
              data-analytics-event="cta_clicked"
              data-analytics-label={primary.label.toLowerCase().replace(/\s+/g, "_")}
              data-analytics-section="cta_band"
              data-analytics-placement="primary"
              data-analytics-destination={primary.href}
            >
              {primary.label}
              <ArrowRight className="size-4" />
            </Link>
          </Button>
          {secondary && (
            <Button
              asChild
              size="lg"
              variant="outline"
              className="h-12 rounded-md border-border bg-transparent px-6"
            >
              <Link
                href={secondary.href}
                data-analytics-event="cta_clicked"
                data-analytics-label={secondary.label.toLowerCase().replace(/\s+/g, "_")}
                data-analytics-section="cta_band"
                data-analytics-placement="secondary"
                data-analytics-destination={secondary.href}
              >
                {secondary.label}
              </Link>
            </Button>
          )}
        </div>
      </div>
    </section>
  );
}

/** Simple prose wrapper for legal / long-form text pages. */
export function Prose({ children }: { children: React.ReactNode }) {
  return (
    <div className="mx-auto max-w-3xl px-5 py-16 sm:px-8 sm:py-20">
      <div className="space-y-6 text-sm leading-relaxed text-muted-foreground [&_h2]:mt-10 [&_h2]:font-heading [&_h2]:text-xl [&_h2]:font-semibold [&_h2]:text-foreground [&_h3]:mt-6 [&_h3]:font-semibold [&_h3]:text-foreground [&_a]:text-brand [&_a]:underline-offset-4 hover:[&_a]:underline [&_ul]:list-disc [&_ul]:pl-6 [&_li]:mt-1">
        {children}
      </div>
    </div>
  );
}
