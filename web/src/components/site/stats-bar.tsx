import Link from "next/link";
import { ArrowRight } from "lucide-react";
import { getNetworkStats } from "@/lib/data/stats";
import { formatNumber, formatCspr } from "@/lib/format";

export async function StatsBar() {
  const stats = await getNetworkStats();

  const items = [
    { label: "Agents Online", value: formatNumber(stats.agentsOnline) },
    { label: "Transactions", value: formatNumber(stats.transactions) },
    { label: "Proposals", value: formatNumber(stats.proposals) },
    { label: "TVL on Casper", value: formatCspr(stats.tvlCspr) },
  ];

  return (
    <section
      aria-label="Live network statistics"
      className="relative z-10 border-y border-border bg-background/70 backdrop-blur-xl"
    >
      <div className="mx-auto flex max-w-7xl items-center gap-0 overflow-x-auto px-5 py-3.5 sm:px-8">
        {/* Live indicator */}
        <div className="flex shrink-0 items-center gap-2 whitespace-nowrap pr-6">
          <span className="relative flex size-2">
            <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-brand opacity-75" />
            <span className="relative inline-flex size-2 rounded-full bg-brand" />
          </span>
          <span className="text-[11px] font-semibold uppercase tracking-[0.18em] text-foreground">
            Live Network
          </span>
          <ArrowRight className="size-3 text-brand" aria-hidden />
        </div>

        {/* Metrics with hairline dividers */}
        <dl className="flex flex-1 items-center">
          {items.map((item) => (
            <div
              key={item.label}
              className="flex shrink-0 items-baseline gap-2 whitespace-nowrap border-l border-border px-6"
            >
              <dt className="text-[11px] font-medium uppercase tracking-wider text-muted-foreground">
                {item.label}
              </dt>
              <dd className="font-mono text-sm font-semibold tabular-nums text-foreground">
                {item.value}
              </dd>
            </div>
          ))}
        </dl>

        {/* Dashboard CTA */}
        <Link
          href="/status"
          className="group ml-6 inline-flex shrink-0 cursor-pointer items-center gap-2 whitespace-nowrap rounded-md border border-brand/30 bg-brand/10 py-2 pl-4 pr-2 text-[11px] font-semibold uppercase tracking-wider text-foreground transition-colors hover:bg-brand/20 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand/50"
        >
          View Live Dashboard
          <span className="flex size-5 items-center justify-center rounded-full bg-brand text-primary-foreground transition-transform group-hover:translate-x-0.5">
            <ArrowRight className="size-3" aria-hidden />
          </span>
        </Link>
      </div>
    </section>
  );
}
