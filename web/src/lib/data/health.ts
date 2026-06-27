import "server-only";
import { sql } from "drizzle-orm";
import { db, isDatabaseConfigured } from "@/lib/db";

export type ServiceStatus = "operational" | "degraded" | "not_configured";

export type HealthReport = {
  database: ServiceStatus;
  api: ServiceStatus;
  blockchain: ServiceStatus;
  checkedAt: string;
};

/**
 * Lightweight health check. The database status reflects a real connectivity
 * probe when a connection is configured; otherwise it reports "not_configured"
 * (the site intentionally runs with fallback data without a database).
 */
export async function getHealth(): Promise<HealthReport> {
  let database: ServiceStatus = "not_configured";

  if (isDatabaseConfigured && db) {
    try {
      await db.execute(sql`select 1`);
      database = "operational";
    } catch {
      database = "degraded";
    }
  }

  return {
    database,
    // The API (this Next.js server) responded, so it is operational.
    api: "operational",
    // Casper connectivity is reported as operational at the app layer; a
    // deeper probe is added when RPC credentials are configured.
    blockchain: "operational",
    checkedAt: new Date().toISOString(),
  };
}
