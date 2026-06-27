import "server-only";
import {
  S3Client,
  PutObjectCommand,
  DeleteObjectCommand,
  type ObjectCannedACL,
} from "@aws-sdk/client-s3";

/**
 * S3-compatible object storage for media uploads.
 *
 * Works with both Cloudflare R2 and Amazon S3 (R2 implements the S3 API).
 *
 * Env:
 *   S3_BUCKET             bucket name
 *   S3_ACCESS_KEY_ID      access key
 *   S3_SECRET_ACCESS_KEY  secret key
 *   S3_REGION             "auto" for R2, e.g. "us-east-1" for AWS
 *   S3_ENDPOINT           R2: https://<account>.r2.cloudflarestorage.com (omit for AWS)
 *   S3_PUBLIC_BASE_URL    public base URL for objects (R2 public domain / CloudFront / custom)
 *   S3_FORCE_PATH_STYLE   "true" to force path-style (often needed for R2/minio)
 *   S3_ACL                optional canned ACL, e.g. "public-read" (AWS; R2 ignores)
 */

const {
  S3_BUCKET,
  S3_ACCESS_KEY_ID,
  S3_SECRET_ACCESS_KEY,
  S3_REGION,
  S3_ENDPOINT,
  S3_PUBLIC_BASE_URL,
  S3_FORCE_PATH_STYLE,
  S3_ACL,
} = process.env;

export function isStorageConfigured(): boolean {
  return Boolean(
    S3_BUCKET && S3_ACCESS_KEY_ID && S3_SECRET_ACCESS_KEY && S3_PUBLIC_BASE_URL,
  );
}

export function storageInfo() {
  return {
    configured: isStorageConfigured(),
    provider: S3_ENDPOINT?.includes("r2.cloudflarestorage.com")
      ? "Cloudflare R2"
      : S3_ENDPOINT
        ? "S3-compatible"
        : "Amazon S3",
    bucket: S3_BUCKET ?? null,
    publicBaseUrl: S3_PUBLIC_BASE_URL ?? null,
  };
}

let client: S3Client | null = null;

function getClient(): S3Client {
  if (!isStorageConfigured()) {
    throw new Error("Storage is not configured.");
  }
  if (!client) {
    client = new S3Client({
      region: S3_REGION || "auto",
      endpoint: S3_ENDPOINT || undefined,
      forcePathStyle: S3_FORCE_PATH_STYLE === "true",
      credentials: {
        accessKeyId: S3_ACCESS_KEY_ID as string,
        secretAccessKey: S3_SECRET_ACCESS_KEY as string,
      },
    });
  }
  return client;
}

export function publicUrl(key: string): string {
  const base = (S3_PUBLIC_BASE_URL ?? "").replace(/\/$/, "");
  return `${base}/${key}`;
}

export async function uploadObject(params: {
  key: string;
  body: Uint8Array | Buffer;
  contentType: string;
}): Promise<{ url: string }> {
  await getClient().send(
    new PutObjectCommand({
      Bucket: S3_BUCKET,
      Key: params.key,
      Body: params.body,
      ContentType: params.contentType,
      CacheControl: "public, max-age=31536000, immutable",
      ...(S3_ACL ? { ACL: S3_ACL as ObjectCannedACL } : {}),
    }),
  );
  return { url: publicUrl(params.key) };
}

export async function deleteObject(key: string): Promise<void> {
  await getClient().send(
    new DeleteObjectCommand({ Bucket: S3_BUCKET, Key: key }),
  );
}
