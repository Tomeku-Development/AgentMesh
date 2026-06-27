import "server-only";
import { marked } from "marked";
import { asc, desc, eq } from "drizzle-orm";
import { db } from "@/lib/db";
import { docPages, type DocPage } from "@/lib/db/schema";

marked.setOptions({ gfm: true, breaks: false });

/** Render trusted (admin-authored) Markdown to HTML. */
export function renderMarkdown(md: string): string {
  return marked.parse(md, { async: false }) as string;
}

export async function getPublishedDocs(): Promise<DocPage[]> {
  if (!db) return [];
  try {
    return await db
      .select()
      .from(docPages)
      .where(eq(docPages.published, true))
      .orderBy(asc(docPages.category), asc(docPages.sortOrder), asc(docPages.title));
  } catch (error) {
    console.error("[docs] getPublishedDocs failed:", error);
    return [];
  }
}

export async function getDocBySlug(slug: string): Promise<DocPage | null> {
  if (!db) return null;
  try {
    const [row] = await db
      .select()
      .from(docPages)
      .where(eq(docPages.slug, slug))
      .limit(1);
    return row ?? null;
  } catch (error) {
    console.error("[docs] getDocBySlug failed:", error);
    return null;
  }
}

export async function getAllDocsAdmin(): Promise<DocPage[]> {
  if (!db) return [];
  try {
    return await db
      .select()
      .from(docPages)
      .orderBy(asc(docPages.category), asc(docPages.sortOrder), desc(docPages.updatedAt));
  } catch (error) {
    console.error("[docs] getAllDocsAdmin failed:", error);
    return [];
  }
}

export async function getDocById(id: number): Promise<DocPage | null> {
  if (!db) return null;
  try {
    const [row] = await db
      .select()
      .from(docPages)
      .where(eq(docPages.id, id))
      .limit(1);
    return row ?? null;
  } catch (error) {
    console.error("[docs] getDocById failed:", error);
    return null;
  }
}

/** Group docs by category, preserving order. */
export function groupByCategory(docs: DocPage[]): { category: string; docs: DocPage[] }[] {
  const map = new Map<string, DocPage[]>();
  for (const doc of docs) {
    const list = map.get(doc.category) ?? [];
    list.push(doc);
    map.set(doc.category, list);
  }
  return Array.from(map.entries()).map(([category, docs]) => ({ category, docs }));
}
