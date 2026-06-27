import { getMediaAssets } from "@/lib/data/admin";
import { storageInfo } from "@/lib/storage";
import { MediaManager } from "./media-manager";

export const dynamic = "force-dynamic";

export default async function AdminMediaPage() {
  const [assets, storage] = await Promise.all([
    getMediaAssets(),
    Promise.resolve(storageInfo()),
  ]);

  return (
    <div className="mx-auto max-w-5xl">
      <header className="mb-8">
        <h1 className="font-heading text-2xl font-bold text-foreground">
          Media
        </h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Upload and manage images on{" "}
          {storage.configured ? storage.provider : "S3-compatible storage"}.
          Copy a URL to use it anywhere on the site.
        </p>
      </header>

      <MediaManager assets={assets} configured={storage.configured} />
    </div>
  );
}
