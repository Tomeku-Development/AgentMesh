"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Loader2 } from "lucide-react";

async function authPost(path: string, body: Record<string, unknown>) {
  const res = await fetch(`/api/auth${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify(body),
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    throw new Error(data?.message || data?.error || "Verification failed.");
  }
  return data;
}

export function TwoFactorVerifyForm() {
  const router = useRouter();
  const [code, setCode] = useState("");
  const [trustDevice, setTrustDevice] = useState(false);
  const [useBackupCode, setUseBackupCode] = useState(false);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function onSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setPending(true);
    setError(null);
    try {
      await authPost(
        useBackupCode
          ? "/two-factor/verify-backup-code"
          : "/two-factor/verify-totp",
        useBackupCode ? { code, trustDevice } : { code, trustDevice },
      );
      router.push("/admin");
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Verification failed.");
    } finally {
      setPending(false);
    }
  }

  return (
    <form onSubmit={onSubmit} className="flex flex-col gap-4">
      <label className="flex flex-col gap-1.5">
        <span className="text-sm font-medium text-foreground">
          {useBackupCode ? "Backup code" : "Authenticator code"}
        </span>
        <input
          value={code}
          onChange={(e) =>
            setCode(
              useBackupCode
                ? e.target.value.trim()
                : e.target.value.replace(/\D/g, "").slice(0, 6),
            )
          }
          inputMode={useBackupCode ? "text" : "numeric"}
          autoComplete="one-time-code"
          required
          className="h-11 rounded-md border border-border bg-background/60 px-4 font-mono text-sm text-foreground outline-none focus:border-brand/60 focus:ring-2 focus:ring-brand/30"
        />
      </label>

      <label className="flex items-center gap-2 text-sm text-muted-foreground">
        <input
          type="checkbox"
          checked={trustDevice}
          onChange={(e) => setTrustDevice(e.target.checked)}
          className="size-4 rounded border-border bg-background accent-brand"
        />
        Trust this device for 30 days
      </label>

      {error && (
        <p className="text-sm text-destructive" aria-live="polite">
          {error}
        </p>
      )}

      <button
        type="submit"
        disabled={pending || code.length === 0}
        className="inline-flex h-11 cursor-pointer items-center justify-center gap-2 rounded-md bg-brand text-sm font-semibold text-primary-foreground transition-all hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-60"
      >
        {pending ? <Loader2 className="size-4 animate-spin" /> : "Verify"}
      </button>

      <button
        type="button"
        onClick={() => {
          setUseBackupCode((value) => !value);
          setCode("");
          setError(null);
        }}
        className="text-sm text-brand hover:underline"
      >
        {useBackupCode ? "Use authenticator code" : "Use a backup code"}
      </button>
    </form>
  );
}
