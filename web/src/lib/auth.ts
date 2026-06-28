import { betterAuth } from "better-auth";
import { APIError, createAuthMiddleware, getSessionFromCtx } from "better-auth/api";
import { drizzleAdapter } from "better-auth/adapters/drizzle";
import {
  admin,
  lastLoginMethod,
  organization,
  twoFactor,
} from "better-auth/plugins";
import { nextCookies } from "better-auth/next-js";
import { apiKey } from "@better-auth/api-key";
import { passkey } from "@better-auth/passkey";
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

function originOf(url: string | undefined): string | null {
  if (!url) return null;
  try {
    return new URL(url).origin;
  } catch {
    return null;
  }
}

function hostnameOf(url: string | undefined): string | null {
  if (!url) return null;
  try {
    return new URL(url).hostname;
  } catch {
    return null;
  }
}

const deploymentUrl = process.env.VERCEL_URL
  ? `https://${process.env.VERCEL_URL}`
  : undefined;
const authBaseURL =
  process.env.BETTER_AUTH_URL ||
  process.env.NEXT_PUBLIC_SITE_URL ||
  deploymentUrl ||
  (process.env.NODE_ENV === "production"
    ? "https://www.agentmesh.world"
    : "http://localhost:3000");

const trustedOrigins = Array.from(
  new Set(
    [
      originOf(authBaseURL),
      originOf(deploymentUrl),
      "https://www.agentmesh.world",
      "https://agentmesh.world",
      "http://localhost:3000",
      ...(process.env.BETTER_AUTH_TRUSTED_ORIGINS ?? "")
        .split(",")
        .map((origin) => origin.trim())
        .filter(Boolean),
    ].filter(Boolean) as string[],
  ),
);

const adminOnlyPluginEndpoints = [
  "/passkey/generate-register-options",
  "/passkey/verify-registration",
  "/passkey/list-user-passkeys",
  "/passkey/delete-passkey",
  "/passkey/update-passkey",
];

const adminOnlyAuthPlugin = {
  id: "agentmesh-admin-only-auth-plugin-endpoints" as const,
  hooks: {
    before: [
      {
        matcher(context: { path?: string }) {
          const path = context.path ?? "";
          return (
            path.startsWith("/api-key/") ||
            path.startsWith("/organization/") ||
            adminOnlyPluginEndpoints.includes(path)
          );
        },
        handler: createAuthMiddleware(async (ctx) => {
          const session = await getSessionFromCtx(ctx);
          if (session?.user.role !== "admin") {
            throw APIError.fromStatus("FORBIDDEN");
          }
        }),
      },
    ],
  },
};

export const auth = betterAuth({
  appName: "AgentMesh",
  baseURL: authBaseURL,
  trustedOrigins,
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
    freshAge: 60 * 15, // sensitive actions require a recent session
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
  plugins: [
    adminOnlyAuthPlugin,
    admin(),
    lastLoginMethod({
      storeInDatabase: true,
    }),
    organization({
      allowUserToCreateOrganization: (user) => user.role === "admin",
      organizationLimit: 3,
      membershipLimit: 25,
      invitationLimit: 25,
      teams: {
        enabled: true,
        maximumTeams: 10,
      },
    }),
    apiKey({
      defaultPrefix: "agm_",
      requireName: true,
      enableMetadata: true,
      keyExpiration: {
        defaultExpiresIn: 1000 * 60 * 60 * 24 * 90,
        maxExpiresIn: 365,
      },
      rateLimit: {
        enabled: true,
        timeWindow: 1000 * 60,
        maxRequests: 120,
      },
    }),
    passkey({
      rpName: "AgentMesh",
      rpID: hostnameOf(authBaseURL) ?? "localhost",
      origin: trustedOrigins,
    }),
    twoFactor({
      issuer: "AgentMesh",
      totpOptions: {
        digits: 6,
        period: 30,
      },
      backupCodeOptions: {
        amount: 10,
        length: 10,
        storeBackupCodes: "encrypted",
      },
      accountLockout: {
        enabled: true,
        maxFailedAttempts: 10,
        durationSeconds: 15 * 60,
      },
    }),
    nextCookies(),
  ],
});

export type Session = typeof auth.$Infer.Session;
