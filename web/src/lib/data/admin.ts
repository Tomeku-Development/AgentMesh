import "server-only";
import { desc, sql } from "drizzle-orm";
import { db } from "@/lib/db";
import {
  subscribers,
  contactSubmissions,
  mediaAssets,
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
};

export async function getAdminCounts(): Promise<AdminCounts> {
  if (!db) return { subscribers: 0, messages: 0, media: 0 };
  try {
    const [[s], [m], [a]] = await Promise.all([
      db.select({ c: sql<number>`count(*)::int` }).from(subscribers),
      db.select({ c: sql<number>`count(*)::int` }).from(contactSubmissions),
      db.select({ c: sql<number>`count(*)::int` }).from(mediaAssets),
    ]);
    return { subscribers: s.c, messages: m.c, media: a.c };
  } catch (error) {
    console.error("[admin] getAdminCounts failed:", error);
    return { subscribers: 0, messages: 0, media: 0 };
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
