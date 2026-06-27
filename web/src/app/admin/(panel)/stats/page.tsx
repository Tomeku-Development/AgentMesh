import { getNetworkStats } from "@/lib/data/stats";
import { isDatabaseConfigured } from "@/lib/db";
import { StatsForm } from "./stats-form";

export const dynamic = "force-dynamic";

export default async function AdminStatsPage() {
  const stats = await getNetworkStats();

  return (
    <div className="mx-auto max-w-3xl">
      <header className="mb-8">
        <h1 className="font-heading text-2xl font-bold text-foreground">
          Network Stats
        </h1>
        <p className="mt-1 text-sm text-muted-foreground">
          These power the live stats bar on the homepage and the Status page.
        </p>
      </header>

      {!isDatabaseConfigured && (
        <div className="mb-6 rounded-xl border border-warning/30 bg-warning/10 p-4 text-sm text-warning">
          Database not configured. Set <code>DATABASE_URL</code> to persist
          stats. Showing fallback values.
        </div>
      )}

      <StatsForm
        values={{
          agentsOnline: stats.agentsOnline,
          transactions: stats.transactions,
          proposals: stats.proposals,
          tvlCspr: stats.tvlCspr,
        }}
      />
    </div>
  );
}
