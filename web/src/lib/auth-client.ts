"use client";

import { createAuthClient } from "better-auth/react";
import {
  adminClient,
  lastLoginMethodClient,
  organizationClient,
  twoFactorClient,
} from "better-auth/client/plugins";
import { apiKeyClient } from "@better-auth/api-key/client";
import { passkeyClient } from "@better-auth/passkey/client";

/**
 * Browser auth client. baseURL defaults to the current origin, which serves
 * the BetterAuth handler at /api/auth.
 */
export const authClient = createAuthClient({
  plugins: [
    adminClient(),
    lastLoginMethodClient(),
    organizationClient(),
    apiKeyClient(),
    passkeyClient(),
    twoFactorClient({ twoFactorPage: "/admin/two-factor" }),
  ],
});

export const { signIn, signUp, signOut, useSession } = authClient;
