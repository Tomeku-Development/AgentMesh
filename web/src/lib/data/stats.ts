import "server-only";
import { desc } from "drizzle-orm";
import { db } from "@/lib/db";
import { networkStats, type NetworkStats } from "@/lib/db/schema";

/**
 * Fallback values used when the database is not configured or empty.
 * These keep the landing page fully rendered out of the box.
 */
const FALLBACK_STATS: Pick<
  NetworkStats,
  "agentsOnline" | "transactions" | "proposals" | "tvlCspr"
> = {
  agentsOnline: 1274,
  transactions: 24392,
  proposals: 892,
  tvlCspr: 2_450_000,
};

export type LiveStats = typeof FALLBACK_STATS & { live: boolean };

export async function getNetworkStats(): Promise<LiveStats> {
  if (!db) {
    return { ...FALLBACK_STATS, live: false };
  }

  try {
    const [row] = await db
      .select()
      .from(networkStats)
      .orderBy(desc(networkStats.updatedAt))
      .limit(1);

    if (!row) {
      return { ...FALLBACK_STATS, live: false };
    }

    return {
      agentsOnline: row.agentsOnline,
      transactions: row.transactions,
      proposals: row.proposals,
      tvlCspr: row.tvlCspr,
      live: true,
    };
  } catch (error) {
    // Never let a transient DB issue break the landing page render.
    console.error("[stats] failed to load network stats:", error);
    return { ...FALLBACK_STATS, live: false };
  }
}
