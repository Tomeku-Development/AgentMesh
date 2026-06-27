/**
 * Seed script — inserts an initial network_stats row.
 *
 * Run with:  npm run db:seed
 * Requires DATABASE_URL (loaded from .env.local via --env-file).
 */
import postgres from "postgres";
import { drizzle } from "drizzle-orm/postgres-js";
import { networkStats } from "./schema.ts";

async function main() {
  const url = process.env.DATABASE_URL;
  if (!url) {
    console.error(
      "DATABASE_URL is not set. Add it to .env.local before seeding.",
    );
    process.exit(1);
  }

  const client = postgres(url, { max: 1 });
  const db = drizzle(client);

  await db.insert(networkStats).values({
    agentsOnline: 1274,
    transactions: 24392,
    proposals: 892,
    tvlCspr: 2_450_000,
  });

  console.log("✓ Seeded network_stats");
  await client.end();
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
