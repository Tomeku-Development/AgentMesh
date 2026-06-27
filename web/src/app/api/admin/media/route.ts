import { NextResponse } from "next/server";
import { db } from "@/lib/db";
import { mediaAssets } from "@/lib/db/schema";
import { isStorageConfigured, uploadObject } from "@/lib/storage";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

const MAX_BYTES = 10 * 1024 * 1024; // 10 MB
const ALLOWED = new Set([
  "image/png",
  "image/jpeg",
  "image/webp",
  "image/gif",
  "image/svg+xml",
  "image/avif",
]);

function slugify(name: string) {
  const dot = name.lastIndexOf(".");
  const base = (dot > 0 ? name.slice(0, dot) : name)
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .slice(0, 60);
  const ext = dot > 0 ? name.slice(dot).toLowerCase() : "";
  return `${base || "file"}${ext}`;
}

export async function POST(req: Request) {
  if (!isStorageConfigured()) {
    return NextResponse.json(
      { error: "Storage is not configured. Set S3 / R2 env vars." },
      { status: 503 },
    );
  }
  if (!db) {
    return NextResponse.json(
      { error: "Database is not configured." },
      { status: 503 },
    );
  }

  let form: FormData;
  try {
    form = await req.formData();
  } catch {
    return NextResponse.json({ error: "Invalid form data." }, { status: 400 });
  }

  const file = form.get("file");
  const alt = String(form.get("alt") ?? "").slice(0, 300) || null;

  if (!(file instanceof File)) {
    return NextResponse.json({ error: "No file provided." }, { status: 400 });
  }
  if (!ALLOWED.has(file.type)) {
    return NextResponse.json(
      { error: `Unsupported type: ${file.type || "unknown"}.` },
      { status: 415 },
    );
  }
  if (file.size > MAX_BYTES) {
    return NextResponse.json(
      { error: "File exceeds 10 MB limit." },
      { status: 413 },
    );
  }

  const year = new Date().getFullYear();
  const key = `uploads/${year}/${crypto.randomUUID()}-${slugify(file.name)}`;
  const body = Buffer.from(await file.arrayBuffer());

  try {
    const { url } = await uploadObject({
      key,
      body,
      contentType: file.type,
    });

    const [row] = await db
      .insert(mediaAssets)
      .values({
        key,
        url,
        filename: file.name.slice(0, 256),
        contentType: file.type,
        size: file.size,
        alt,
      })
      .returning();

    return NextResponse.json({ asset: row }, { status: 201 });
  } catch (error) {
    console.error("[admin/media] upload failed:", error);
    return NextResponse.json({ error: "Upload failed." }, { status: 500 });
  }
}
