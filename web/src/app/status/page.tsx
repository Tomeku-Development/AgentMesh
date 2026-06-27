import type { Metadata } from "next";
import { PageHero, Section, SectionTitle } from "@/components/site/page-parts";
import { getHealth, type ServiceStatus } from "@/lib/data/health";
import { getNetworkStats } from "@/lib/data/stats";
import { formatNumber, formatCspr } from "@/lib/format";
import { cn } from "@/lib/utils";

export const metadata: Metadata = {
  title: "Status — AgentMesh",
  description:
    "Live operational status for AgentMesh services and the Casper network connection.",
};

// Always render fresh status.
export const dynamic = "force-dynamic";

const statusMeta: Record<
  ServiceStatus,
  { label: string; dot: string; text: string }
> = {
  operational: {
    label: "Operational",
    dot: "bg-success",
    text: "text-success",
  },
  degraded: {
    label: "Degraded",
    dot: "bg-destructive",
    text: "text-destructive",
  },
  not_configured: {
    label: "Not configured",
    dot: "bg-warning",
    text: "text-warning",
  },
};

export default async function StatusPage() {
  const [health, stats] = await Promise.all([getHealth(), getNetworkStats()]);

  const services: { name: string; status: ServiceStatus; note?: string }[] = [
    { name: "Web / API", status: health.api },
    {
      name: "Database (PostgreSQL)",
      status: health.database,
      note:
        health.database === "not_configured"
          ? "Running with fallback data — set DATABASE_URL to enable."
          : undefined,
    },
    { name: "Casper Network", status: health.blockchain },
  ];

  const allOk = services.every((s) => s.status !== "degraded");

  const metrics = [
    { label: "Agents Online", value: formatNumber(stats.agentsOnline) },
    { label: "Transactions", value: formatNumber(stats.transactions) },
    { label: "Proposals", value: formatNumber(stats.proposals) },
    { label: "TVL on Casper", value: formatCspr(stats.tvlCspr) },
  ];

  return (
    <>
      <PageHero
        eyebrow="Status"
        title="System status"
        description="Live operational status for AgentMesh services. This page is checked on every request."
      >
        <div className="inline-flex items-center gap-2.5 rounded-full border border-border bg-card px-4 py-2">
          <span
            className={cn(
              "size-2.5 rounded-full",
              allOk ? "bg-success" : "bg-destructive",
            )}
          />
          <span className="text-sm font-semibold text-foreground">
            {allOk ? "All systems operational" : "Some systems degraded"}
          </span>
        </div>
      </PageHero>

      <Section>
        <SectionTitle eyebrow="Services" title="Component status" />
        <div className="mt-8 overflow-hidden rounded-xl border border-border">
          {services.map((s, i) => {
            const meta = statusMeta[s.status];
            return (
              <div
                key={s.name}
                className={cn(
                  "flex items-center justify-between gap-4 bg-card p-5",
                  i !== 0 && "border-t border-border",
                )}
              >
                <div>
                  <p className="font-medium text-foreground">{s.name}</p>
                  {s.note && (
                    <p className="mt-0.5 text-xs text-muted-foreground">
                      {s.note}
                    </p>
                  )}
                </div>
                <span
                  className={cn(
                    "inline-flex items-center gap-2 text-sm font-medium",
                    meta.text,
                  )}
                >
                  <span className={cn("size-2 rounded-full", meta.dot)} />
                  {meta.label}
                </span>
              </div>
            );
          })}
        </div>
        <p className="mt-4 text-xs text-muted-foreground">
          Last checked {new Date(health.checkedAt).toLocaleString()} ·{" "}
          <a
            href="/api/health"
            className="text-brand underline-offset-4 hover:underline"
          >
            /api/health
          </a>
        </p>
      </Section>

      <Section className="border-t border-border bg-secondary/20">
        <SectionTitle
          eyebrow="Network"
          title="Live metrics"
          description={
            stats.live
              ? "Live from the database."
              : "Representative values (database not connected)."
          }
        />
        <div className="mt-8 grid grid-cols-2 gap-px overflow-hidden rounded-xl border border-border bg-border sm:grid-cols-4">
          {metrics.map((m) => (
            <div key={m.label} className="bg-card p-6">
              <p className="text-[11px] font-medium uppercase tracking-wider text-muted-foreground">
                {m.label}
              </p>
              <p className="mt-1 font-mono text-lg font-semibold tabular-nums text-foreground">
                {m.value}
              </p>
            </div>
          ))}
        </div>
      </Section>
    </>
  );
}
