import "server-only";
import { headers } from "next/headers";
import { redirect } from "next/navigation";
import { count } from "drizzle-orm";
import { auth } from "@/lib/auth";
import { db } from "@/lib/db";
import { user as userTable } from "@/lib/db/auth-schema";

export async function getSession() {
  return auth.api.getSession({ headers: await headers() });
}

/** Return the current session only when it belongs to an admin user. */
export async function getAdminSession() {
  const session = await getSession();
  if (!session || session.user.role !== "admin") return null;
  return session;
}

/** Require an authenticated admin; redirect to login otherwise. */
export async function requireAdmin() {
  const session = await getSession();
  if (!session) redirect("/admin/login");
  if (session.user.role !== "admin") redirect("/admin/login?error=forbidden");
  return session;
}

/** Whether any user exists (used to gate first-admin bootstrap). */
export async function userCount(): Promise<number> {
  if (!db) return 0;
  try {
    const [{ value }] = await db.select({ value: count() }).from(userTable);
    return value;
  } catch {
    return 0;
  }
}
