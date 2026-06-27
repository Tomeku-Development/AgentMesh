"use server";

import { headers } from "next/headers";
import { redirect } from "next/navigation";
import { revalidatePath } from "next/cache";
import { eq } from "drizzle-orm";
import { db } from "@/lib/db";
import { networkStats, siteContent, mediaAssets, docPages } from "@/lib/db/schema";
import { auth } from "@/lib/auth";
import { CONTENT_FIELDS } from "@/lib/data/site-content";
import { deleteObject } from "@/lib/storage";

export type SaveState = {
  status: "idle" | "success" | "error";
  message: string;
};

/* --------------------------- Content ----------------------------- */

export async function saveContent(
  _prev: SaveState,
  formData: FormData,
): Promise<SaveState> {
  if (!db) {
    return {
      status: "error",
      message: "Database not configured. Set DATABASE_URL to edit content.",
    };
  }

  try {
    let saved = 0;
    for (const field of CONTENT_FIELDS) {
      if (!formData.has(field.key)) continue;
      const value = String(formData.get(field.key) ?? "");
      await db
        .insert(siteContent)
        .values({ key: field.key, value, updatedAt: new Date() })
        .onConflictDoUpdate({
          target: siteContent.key,
          set: { value, updatedAt: new Date() },
        });
      saved++;
    }
    revalidatePath("/", "layout");
    revalidatePath("/admin/content");
    revalidatePath("/admin/settings");
    return {
      status: "success",
      message: saved > 0 ? "Saved." : "Nothing to update.",
    };
  } catch (error) {
    console.error("[admin] saveContent failed:", error);
    return { status: "error", message: "Failed to save content." };
  }
}

/* ----------------------------- Stats ----------------------------- */

export async function saveStats(
  _prev: SaveState,
  formData: FormData,
): Promise<SaveState> {
  if (!db) {
    return {
      status: "error",
      message: "Database not configured. Set DATABASE_URL to edit stats.",
    };
  }

  const num = (k: string) =>
    Math.max(0, Math.round(Number(formData.get(k) ?? 0)));
  const values = {
    agentsOnline: num("agentsOnline"),
    transactions: num("transactions"),
    proposals: num("proposals"),
    tvlCspr: num("tvlCspr"),
    updatedAt: new Date(),
  };

  try {
    const [existing] = await db.select().from(networkStats).limit(1);
    if (existing) {
      await db
        .update(networkStats)
        .set(values)
        .where(eq(networkStats.id, existing.id));
    } else {
      await db.insert(networkStats).values(values);
    }
    revalidatePath("/");
    revalidatePath("/status");
    revalidatePath("/admin/stats");
    return { status: "success", message: "Network stats updated." };
  } catch (error) {
    console.error("[admin] saveStats failed:", error);
    return { status: "error", message: "Failed to update stats." };
  }
}

/* ----------------------------- Media ----------------------------- */

export async function deleteMedia(formData: FormData): Promise<void> {
  if (!db) return;
  const id = Number(formData.get("id"));
  const key = String(formData.get("key") ?? "");
  if (!Number.isFinite(id)) return;

  try {
    if (key) await deleteObject(key);
  } catch (error) {
    console.error("[admin] deleteObject failed:", error);
  }
  try {
    await db.delete(mediaAssets).where(eq(mediaAssets.id, id));
  } catch (error) {
    console.error("[admin] deleteMedia row failed:", error);
  }
  revalidatePath("/admin/media");
}

/* ----------------------------- Users ----------------------------- */

export async function createUserAction(
  _prev: SaveState,
  formData: FormData,
): Promise<SaveState> {
  const name = String(formData.get("name") ?? "").trim();
  const email = String(formData.get("email") ?? "")
    .trim()
    .toLowerCase();
  const password = String(formData.get("password") ?? "");
  const role = String(formData.get("role") ?? "user") === "admin" ? "admin" : "user";

  if (name.length < 2) return { status: "error", message: "Enter a name." };
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email))
    return { status: "error", message: "Enter a valid email." };
  if (password.length < 8)
    return { status: "error", message: "Password must be 8+ characters." };

  try {
    await auth.api.createUser({
      body: { name, email, password, role },
      headers: await headers(),
    });
    revalidatePath("/admin/users");
    return { status: "success", message: `Created ${email}.` };
  } catch (error) {
    console.error("[admin] createUser failed:", error);
    return {
      status: "error",
      message:
        error instanceof Error ? error.message : "Failed to create user.",
    };
  }
}

export async function setUserRoleAction(formData: FormData): Promise<void> {
  const userId = String(formData.get("userId") ?? "");
  const role =
    String(formData.get("role") ?? "user") === "admin" ? "admin" : "user";
  if (!userId) return;
  try {
    await auth.api.setRole({
      body: { userId, role },
      headers: await headers(),
    });
  } catch (error) {
    console.error("[admin] setRole failed:", error);
  }
  revalidatePath("/admin/users");
}

export async function setUserBanAction(formData: FormData): Promise<void> {
  const userId = String(formData.get("userId") ?? "");
  const ban = String(formData.get("ban") ?? "") === "1";
  if (!userId) return;
  try {
    if (ban) {
      await auth.api.banUser({
        body: { userId },
        headers: await headers(),
      });
    } else {
      await auth.api.unbanUser({
        body: { userId },
        headers: await headers(),
      });
    }
  } catch (error) {
    console.error("[admin] ban/unban failed:", error);
  }
  revalidatePath("/admin/users");
}

export async function deleteUserAction(formData: FormData): Promise<void> {
  const userId = String(formData.get("userId") ?? "");
  if (!userId) return;
  try {
    await auth.api.removeUser({
      body: { userId },
      headers: await headers(),
    });
  } catch (error) {
    console.error("[admin] removeUser failed:", error);
  }
  revalidatePath("/admin/users");
}

/* ------------------------------ Docs ----------------------------- */

function slugify(input: string): string {
  return input
    .toLowerCase()
    .trim()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .slice(0, 160);
}

export async function saveDoc(
  _prev: SaveState,
  formData: FormData,
): Promise<SaveState> {
  if (!db) {
    return { status: "error", message: "Database not configured." };
  }

  const idRaw = formData.get("id");
  const id = idRaw ? Number(idRaw) : null;
  const title = String(formData.get("title") ?? "").trim();
  const slug =
    slugify(String(formData.get("slug") ?? "")) || slugify(title);
  const category = String(formData.get("category") ?? "General").trim() || "General";
  const summary = String(formData.get("summary") ?? "").trim();
  const body = String(formData.get("body") ?? "");
  const sortOrder = Math.round(Number(formData.get("sortOrder") ?? 0)) || 0;
  const published = formData.get("published") === "on";
  const seoTitle = String(formData.get("seoTitle") ?? "").trim() || null;
  const seoDescription =
    String(formData.get("seoDescription") ?? "").trim() || null;

  if (title.length < 2) return { status: "error", message: "Title is required." };
  if (!slug) return { status: "error", message: "Slug is required." };
  if (slug === "api")
    return { status: "error", message: '"api" is a reserved slug.' };

  const values = {
    slug,
    title,
    category,
    summary,
    body,
    sortOrder,
    published,
    seoTitle,
    seoDescription,
    updatedAt: new Date(),
  };

  try {
    if (id) {
      await db.update(docPages).set(values).where(eq(docPages.id, id));
    } else {
      await db.insert(docPages).values(values);
    }
  } catch (error) {
    console.error("[admin] saveDoc failed:", error);
    const msg =
      error instanceof Error && /unique|duplicate/i.test(error.message)
        ? "That slug is already in use."
        : "Failed to save document.";
    return { status: "error", message: msg };
  }

  revalidatePath("/docs");
  revalidatePath(`/docs/${slug}`);
  revalidatePath("/admin/docs");
  redirect("/admin/docs");
}

export async function deleteDoc(formData: FormData): Promise<void> {
  if (!db) return;
  const id = Number(formData.get("id"));
  if (!Number.isFinite(id)) return;
  try {
    await db.delete(docPages).where(eq(docPages.id, id));
  } catch (error) {
    console.error("[admin] deleteDoc failed:", error);
  }
  revalidatePath("/docs");
  revalidatePath("/admin/docs");
}

export async function toggleDocPublished(formData: FormData): Promise<void> {
  if (!db) return;
  const id = Number(formData.get("id"));
  const next = formData.get("publish") === "1";
  if (!Number.isFinite(id)) return;
  try {
    await db
      .update(docPages)
      .set({ published: next, updatedAt: new Date() })
      .where(eq(docPages.id, id));
  } catch (error) {
    console.error("[admin] toggleDocPublished failed:", error);
  }
  revalidatePath("/docs");
  revalidatePath("/admin/docs");
}
