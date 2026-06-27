import { drizzle } from "drizzle-orm/postgres-js";
import postgres from "postgres";
import * as schema from "./schema";

/**
 * The database connection is created lazily and is optional.
 *
 * The landing page must render even when no DATABASE_URL is configured
 * (e.g. first clone, preview builds), so callers should treat a missing
 * connection as "no data" and fall back to sensible defaults.
 */
const connectionString = process.env.DATABASE_URL;

declare global {
  var __agentmesh_pg__: ReturnType<typeof postgres> | undefined;
}

let client: ReturnType<typeof postgres> | undefined;

if (connectionString) {
  // Reuse the client across HMR reloads in development to avoid exhausting
  // the connection pool.
  client =
    global.__agentmesh_pg__ ??
    postgres(connectionString, {
      max: 10,
      prepare: false,
    });

  if (process.env.NODE_ENV !== "production") {
    global.__agentmesh_pg__ = client;
  }
}

export const db = client ? drizzle(client, { schema }) : null;

export const isDatabaseConfigured = Boolean(client);

export { schema };
