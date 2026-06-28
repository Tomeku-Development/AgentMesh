import "server-only";
import { desc, sql } from "drizzle-orm";
import { db, isDatabaseConfigured } from "@/lib/db";
import { getPaymentProviderStatus } from "@/lib/payments";
import {
  subscribers,
  contactSubmissions,
  mediaAssets,
  paymentTransactions,
  docPages,
  type MediaAsset,
} from "@/lib/db/schema";

export async function getMediaAssets(): Promise<MediaAsset[]> {
  if (!db) return [];
  try {
    return await db
      .select()
      .from(mediaAssets)
      .orderBy(desc(mediaAssets.createdAt));
  } catch (error) {
    console.error("[admin] getMediaAssets failed:", error);
    return [];
  }
}

export async function getSubscribers() {
  if (!db) return [];
  try {
    return await db
      .select()
      .from(subscribers)
      .orderBy(desc(subscribers.createdAt));
  } catch (error) {
    console.error("[admin] getSubscribers failed:", error);
    return [];
  }
}

export async function getContactSubmissions() {
  if (!db) return [];
  try {
    return await db
      .select()
      .from(contactSubmissions)
      .orderBy(desc(contactSubmissions.createdAt));
  } catch (error) {
    console.error("[admin] getContactSubmissions failed:", error);
    return [];
  }
}

export type AdminCounts = {
  subscribers: number;
  messages: number;
  media: number;
  payments: number;
  docsDrafts: number;
};

export async function getAdminCounts(): Promise<AdminCounts> {
  if (!db) {
    return { subscribers: 0, messages: 0, media: 0, payments: 0, docsDrafts: 0 };
  }
  try {
    const [[s], [m], [a], [p], [d]] = await Promise.all([
      db.select({ c: sql<number>`count(*)::int` }).from(subscribers),
      db.select({ c: sql<number>`count(*)::int` }).from(contactSubmissions),
      db.select({ c: sql<number>`count(*)::int` }).from(mediaAssets),
      db.select({ c: sql<number>`count(*)::int` }).from(paymentTransactions),
      db
        .select({ c: sql<number>`count(*)::int` })
        .from(docPages)
        .where(sql`${docPages.published} = false`),
    ]);
    return {
      subscribers: s.c,
      messages: m.c,
      media: a.c,
      payments: p.c,
      docsDrafts: d.c,
    };
  } catch (error) {
    console.error("[admin] getAdminCounts failed:", error);
    return { subscribers: 0, messages: 0, media: 0, payments: 0, docsDrafts: 0 };
  }
}

export type ActivityItem = {
  kind: "subscriber" | "message" | "media";
  title: string;
  subtitle: string;
  at: Date;
};

export async function getRecentActivity(limit = 7): Promise<ActivityItem[]> {
  if (!db) return [];
  try {
    const [subs, msgs, media] = await Promise.all([
      db
        .select()
        .from(subscribers)
        .orderBy(desc(subscribers.createdAt))
        .limit(limit),
      db
        .select()
        .from(contactSubmissions)
        .orderBy(desc(contactSubmissions.createdAt))
        .limit(limit),
      db
        .select()
        .from(mediaAssets)
        .orderBy(desc(mediaAssets.createdAt))
        .limit(limit),
    ]);

    const items: ActivityItem[] = [
      ...subs.map((s) => ({
        kind: "subscriber" as const,
        title: "New subscriber",
        subtitle: s.email,
        at: new Date(s.createdAt),
      })),
      ...msgs.map((m) => ({
        kind: "message" as const,
        title: `Message from ${m.name}`,
        subtitle: m.company ? `${m.email} · ${m.company}` : m.email,
        at: new Date(m.createdAt),
      })),
      ...media.map((a) => ({
        kind: "media" as const,
        title: "Media uploaded",
        subtitle: a.filename,
        at: new Date(a.createdAt),
      })),
    ];

    return items.sort((a, b) => b.at.getTime() - a.at.getTime()).slice(0, limit);
  } catch (error) {
    console.error("[admin] getRecentActivity failed:", error);
    return [];
  }
}

export type AdminNotification = {
  title: string;
  detail: string;
  href: string;
  tone: "info" | "warning" | "success";
};

export async function getAdminNotifications(): Promise<AdminNotification[]> {
  const [counts, activity] = await Promise.all([
    getAdminCounts(),
    getRecentActivity(3),
  ]);
  const notifications: AdminNotification[] = [];

  if (!isDatabaseConfigured) {
    notifications.push({
      title: "Database not configured",
      detail: "Admin data, sales, and reports need DATABASE_URL.",
      href: "/admin/settings",
      tone: "warning",
    });
  }

  const missingProviders = getPaymentProviderStatus()
    .filter((provider) => !provider.configured)
    .map((provider) => provider.label);
  if (missingProviders.length > 0) {
    notifications.push({
      title: "Payment setup incomplete",
      detail: `${missingProviders.join(", ")} still need credentials.`,
      href: "/admin/sales",
      tone: "warning",
    });
  }

  if (counts.messages > 0) {
    notifications.push({
      title: `${counts.messages} sales message${counts.messages === 1 ? "" : "s"}`,
      detail: "Review recent contact requests.",
      href: "/admin/messages",
      tone: "info",
    });
  }

  if (counts.docsDrafts > 0) {
    notifications.push({
      title: `${counts.docsDrafts} draft doc${counts.docsDrafts === 1 ? "" : "s"}`,
      detail: "Draft documentation is waiting to publish.",
      href: "/admin/docs",
      tone: "info",
    });
  }

  for (const item of activity.slice(0, 2)) {
    notifications.push({
      title: item.title,
      detail: item.subtitle,
      href: item.kind === "message" ? "/admin/messages" : "/admin/analytics",
      tone: "success",
    });
  }

  return notifications.slice(0, 6);
}

export async function getPaymentTransactions(limit = 50) {
  if (!db) return [];
  try {
    return await db
      .select()
      .from(paymentTransactions)
      .orderBy(desc(paymentTransactions.createdAt))
      .limit(limit);
  } catch (error) {
    console.error("[admin] getPaymentTransactions failed:", error);
    return [];
  }
}

export async function getAllPaymentTransactions() {
  return getPaymentTransactions(1000);
}
