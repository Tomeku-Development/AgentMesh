"use client";

import { useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { UploadCloud, Loader2, Copy, Check, Trash2 } from "lucide-react";
import { deleteMedia } from "@/app/admin/actions";
import type { MediaAsset } from "@/lib/db/schema";

function formatBytes(bytes: number) {
  if (!bytes) return "0 B";
  const units = ["B", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(bytes) / Math.log(1024));
  return `${(bytes / Math.pow(1024, i)).toFixed(1)} ${units[i]}`;
}

export function MediaManager({
  assets,
  configured,
}: {
  assets: MediaAsset[];
  configured: boolean;
}) {
  const router = useRouter();
  const fileRef = useRef<HTMLInputElement>(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState<number | null>(null);

  async function onUpload(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setError(null);
    const form = e.currentTarget;
    const data = new FormData(form);
    const file = data.get("file");
    if (!(file instanceof File) || file.size === 0) {
      setError("Choose a file to upload.");
      return;
    }

    setUploading(true);
    try {
      const res = await fetch("/api/admin/media", {
        method: "POST",
        body: data,
      });
      const json = await res.json();
      if (!res.ok) {
        setError(json.error ?? "Upload failed.");
      } else {
        form.reset();
        router.refresh();
      }
    } catch {
      setError("Network error during upload.");
    } finally {
      setUploading(false);
    }
  }

  async function copy(asset: MediaAsset) {
    try {
      await navigator.clipboard.writeText(asset.url);
      setCopied(asset.id);
      setTimeout(() => setCopied(null), 1500);
    } catch {
      /* ignore */
    }
  }

  return (
    <div className="flex flex-col gap-8">
      {/* Uploader */}
      <form
        onSubmit={onUpload}
        className="rounded-xl border border-border bg-card p-6"
      >
        {!configured && (
          <div className="mb-4 rounded-lg border border-warning/30 bg-warning/10 p-3 text-sm text-warning">
            Storage is not configured. Set your Cloudflare R2 / Amazon S3 env
            vars to enable uploads.
          </div>
        )}
        <div className="flex flex-col gap-4 sm:flex-row sm:items-end">
          <div className="flex-1">
            <label
              htmlFor="file"
              className="mb-1.5 block text-sm font-medium text-foreground"
            >
              Image file
            </label>
            <input
              ref={fileRef}
              id="file"
              name="file"
              type="file"
              accept="image/png,image/jpeg,image/webp,image/gif,image/svg+xml,image/avif"
              disabled={!configured || uploading}
              className="block w-full cursor-pointer rounded-md border border-border bg-background/60 text-sm text-muted-foreground file:mr-4 file:cursor-pointer file:border-0 file:bg-secondary file:px-4 file:py-2.5 file:text-sm file:font-medium file:text-foreground hover:file:bg-secondary/70 disabled:opacity-50"
            />
          </div>
          <div className="flex-1">
            <label
              htmlFor="alt"
              className="mb-1.5 block text-sm font-medium text-foreground"
            >
              Alt text <span className="text-muted-foreground">(optional)</span>
            </label>
            <input
              id="alt"
              name="alt"
              type="text"
              placeholder="Describe the image"
              disabled={!configured || uploading}
              className="h-11 w-full rounded-md border border-border bg-background/60 px-4 text-sm text-foreground outline-none transition-colors placeholder:text-muted-foreground focus:border-brand/60 focus:ring-2 focus:ring-brand/30 disabled:opacity-50"
            />
          </div>
          <button
            type="submit"
            disabled={!configured || uploading}
            className="inline-flex h-11 cursor-pointer items-center justify-center gap-2 rounded-md bg-brand px-5 text-sm font-semibold text-primary-foreground transition-all hover:brightness-110 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand/50 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {uploading ? (
              <Loader2 className="size-4 animate-spin" />
            ) : (
              <>
                <UploadCloud className="size-4" />
                Upload
              </>
            )}
          </button>
        </div>
        {error && <p className="mt-3 text-sm text-destructive">{error}</p>}
        <p className="mt-3 text-xs text-muted-foreground">
          PNG, JPEG, WebP, GIF, SVG, or AVIF. Max 10 MB.
        </p>
      </form>

      {/* Grid */}
      {assets.length === 0 ? (
        <div className="rounded-xl border border-dashed border-border p-12 text-center text-sm text-muted-foreground">
          No media yet. Upload your first image above.
        </div>
      ) : (
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4">
          {assets.map((asset) => (
            <div
              key={asset.id}
              className="group overflow-hidden rounded-xl border border-border bg-card"
            >
              <div className="relative aspect-square bg-[repeating-conic-gradient(#1a1a1a_0_25%,#111_0_50%)] bg-[length:20px_20px]">
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img
                  src={asset.url}
                  alt={asset.alt ?? asset.filename}
                  className="absolute inset-0 h-full w-full object-contain"
                  loading="lazy"
                />
              </div>
              <div className="flex flex-col gap-2 p-3">
                <p
                  className="truncate text-xs font-medium text-foreground"
                  title={asset.filename}
                >
                  {asset.filename}
                </p>
                <p className="text-[11px] text-muted-foreground">
                  {formatBytes(asset.size)}
                </p>
                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    onClick={() => copy(asset)}
                    className="inline-flex flex-1 cursor-pointer items-center justify-center gap-1.5 rounded-md border border-border bg-background/60 px-2 py-1.5 text-[11px] font-medium text-foreground transition-colors hover:bg-secondary"
                  >
                    {copied === asset.id ? (
                      <>
                        <Check className="size-3 text-success" />
                        Copied
                      </>
                    ) : (
                      <>
                        <Copy className="size-3" />
                        Copy URL
                      </>
                    )}
                  </button>
                  <form action={deleteMedia}>
                    <input type="hidden" name="id" value={asset.id} />
                    <input type="hidden" name="key" value={asset.key} />
                    <button
                      type="submit"
                      aria-label={`Delete ${asset.filename}`}
                      className="inline-flex size-7 cursor-pointer items-center justify-center rounded-md border border-border text-muted-foreground transition-colors hover:border-destructive/40 hover:bg-destructive/10 hover:text-destructive"
                    >
                      <Trash2 className="size-3.5" />
                    </button>
                  </form>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
