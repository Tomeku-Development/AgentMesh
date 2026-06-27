import { betterAuth } from "better-auth";
import { drizzleAdapter } from "better-auth/adapters/drizzle";
import { admin } from "better-auth/plugins";
import { nextCookies } from "better-auth/next-js";
import { count } from "drizzle-orm";
import { db } from "./db";
import * as authSchema from "./db/auth-schema";

/**
 * BetterAuth server instance (email + password, with roles via the admin
 * plugin). The first account ever created is promoted to "admin"; everyone
 * else defaults to "user".
 *
 * Admin requires a database. When DATABASE_URL is unset, importing this module
 * throws on first use, which is intentional — the admin panel needs Postgres.
 */
if (!db) {
  throw new Error(
    "Authentication requires a database. Set DATABASE_URL to use /admin.",
  );
}

const database = db;

export const auth = betterAuth({
  appName: "AgentMesh",
  baseURL: process.env.BETTER_AUTH_URL || "http://localhost:3000",
  secret:
    process.env.BETTER_AUTH_SECRET ||
    process.env.ADMIN_SESSION_SECRET ||
    "agentmesh-dev-secret-change-me",
  database: drizzleAdapter(database, {
    provider: "pg",
    schema: authSchema,
  }),
  emailAndPassword: {
    enabled: true,
    minPasswordLength: 8,
  },
  session: {
    expiresIn: 60 * 60 * 24 * 7, // 7 days
    updateAge: 60 * 60 * 24, // refresh daily
  },
  databaseHooks: {
    user: {
      create: {
        before: async (newUser) => {
          // Promote the very first user to admin.
          const [{ value }] = await database
            .select({ value: count() })
            .from(authSchema.user);
          return {
            data: {
              ...newUser,
              role: value === 0 ? "admin" : "user",
            },
          };
        },
      },
    },
  },
  plugins: [admin(), nextCookies()],
});

export type Session = typeof auth.$Infer.Session;
