"use client";

import { useState } from "react";
import QRCode from "qrcode";
import { Check, Copy, Loader2, ShieldCheck, ShieldOff } from "lucide-react";
import { cn } from "@/lib/utils";

type Step = "idle" | "setup" | "enabled";

async function authPost<T>(path: string, body: Record<string, unknown>): Promise<T> {
  const res = await fetch(`/api/auth${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify(body),
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    throw new Error(data?.message || data?.error || "Request failed.");
  }
  return data as T;
}

export function TwoFactorCard({ enabled }: { enabled: boolean }) {
  const [step, setStep] = useState<Step>(enabled ? "enabled" : "idle");
  const [pending, setPending] = useState(false);
  const [password, setPassword] = useState("");
  const [disablePassword, setDisablePassword] = useState("");
  const [code, setCode] = useState("");
  const [totpURI, setTotpURI] = useState("");
  const [qrDataUrl, setQrDataUrl] = useState("");
  const [backupCodes, setBackupCodes] = useState<string[]>([]);
  const [message, setMessage] = useState<{ kind: "success" | "error"; text: string } | null>(null);

  async function startSetup() {
    setPending(true);
    setMessage(null);
    try {
      const data = await authPost<{ totpURI: string; backupCodes: string[] }>(
        "/two-factor/enable",
        { password, issuer: "AgentMesh" },
      );
      setTotpURI(data.totpURI);
      setQrDataUrl(await QRCode.toDataURL(data.totpURI, { margin: 1, width: 220 }));
      setBackupCodes(data.backupCodes);
      setStep("setup");
    } catch (error) {
      setMessage({
        kind: "error",
        text: error instanceof Error ? error.message : "Could not start 2FA setup.",
      });
    } finally {
      setPending(false);
    }
  }

  async function verifySetup() {
    setPending(true);
    setMessage(null);
    try {
      await authPost("/two-factor/verify-totp", { code });
      setStep("enabled");
      setPassword("");
      setCode("");
      setMessage({ kind: "success", text: "Two-factor authentication enabled." });
    } catch (error) {
      setMessage({
        kind: "error",
        text: error instanceof Error ? error.message : "Invalid authentication code.",
      });
    } finally {
      setPending(false);
    }
  }

  async function disableTwoFactor() {
    setPending(true);
    setMessage(null);
    try {
      await authPost("/two-factor/disable", { password: disablePassword });
      setStep("idle");
      setDisablePassword("");
      setBackupCodes([]);
      setTotpURI("");
      setQrDataUrl("");
      setMessage({ kind: "success", text: "Two-factor authentication disabled." });
    } catch (error) {
      setMessage({
        kind: "error",
        text: error instanceof Error ? error.message : "Could not disable 2FA.",
      });
    } finally {
      setPending(false);
    }
  }

  async function copyBackupCodes() {
    await navigator.clipboard.writeText(backupCodes.join("\n"));
    setMessage({ kind: "success", text: "Backup codes copied." });
  }

  return (
    <section className="rounded-xl border border-border bg-card p-5">
      <div className="flex flex-wrap items-start justify-between gap-4 border-b border-border pb-4">
        <div>
          <h2 className="font-heading text-sm font-semibold text-foreground">
            Two-factor authentication
          </h2>
          <p className="mt-1 text-xs text-muted-foreground">
            Require a 6-digit authenticator code when signing in as an admin.
          </p>
        </div>
        <span
          className={cn(
            "inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-semibold uppercase tracking-wider",
            step === "enabled"
              ? "bg-success/15 text-success"
              : "bg-warning/15 text-warning",
          )}
        >
          {step === "enabled" ? (
            <ShieldCheck className="size-3.5" />
          ) : (
            <ShieldOff className="size-3.5" />
          )}
          {step === "enabled" ? "Enabled" : "Off"}
        </span>
      </div>

      {step === "idle" && (
        <div className="mt-5 max-w-md">
          <label className="flex flex-col gap-1.5">
            <span className="text-sm font-medium text-foreground">
              Confirm password
            </span>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoComplete="current-password"
              className="h-11 rounded-md border border-border bg-background/60 px-4 text-sm text-foreground outline-none focus:border-brand/60 focus:ring-2 focus:ring-brand/30"
            />
          </label>
          <button
            type="button"
            onClick={startSetup}
            disabled={pending || !password}
            className="mt-4 inline-flex h-10 cursor-pointer items-center gap-2 rounded-md bg-brand px-4 text-sm font-semibold text-primary-foreground transition-all hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {pending ? <Loader2 className="size-4 animate-spin" /> : "Set up 2FA"}
          </button>
        </div>
      )}

      {step === "setup" && (
        <div className="mt-5 grid grid-cols-1 gap-6 lg:grid-cols-[260px_1fr]">
          <div>
            {qrDataUrl && (
              // eslint-disable-next-line @next/next/no-img-element
              <img
                src={qrDataUrl}
                alt="Authenticator QR code"
                className="rounded-lg border border-border bg-white p-3"
              />
            )}
          </div>
          <div>
            <p className="text-sm text-foreground">
              Scan the QR code in your authenticator app, then enter the
              6-digit code to finish setup.
            </p>
            <p className="mt-2 break-all rounded-md border border-border bg-background/60 p-3 font-mono text-xs text-muted-foreground">
              {totpURI}
            </p>
            <label className="mt-4 flex max-w-xs flex-col gap-1.5">
              <span className="text-sm font-medium text-foreground">
                Authentication code
              </span>
              <input
                value={code}
                onChange={(e) => setCode(e.target.value.replace(/\D/g, "").slice(0, 6))}
                inputMode="numeric"
                autoComplete="one-time-code"
                className="h-11 rounded-md border border-border bg-background/60 px-4 font-mono text-sm text-foreground outline-none focus:border-brand/60 focus:ring-2 focus:ring-brand/30"
              />
            </label>
            <button
              type="button"
              onClick={verifySetup}
              disabled={pending || code.length !== 6}
              className="mt-4 inline-flex h-10 cursor-pointer items-center gap-2 rounded-md bg-brand px-4 text-sm font-semibold text-primary-foreground transition-all hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {pending ? <Loader2 className="size-4 animate-spin" /> : "Verify and enable"}
            </button>

            {backupCodes.length > 0 && (
              <div className="mt-5 rounded-lg border border-warning/30 bg-warning/10 p-4">
                <div className="flex items-center justify-between gap-3">
                  <p className="text-sm font-medium text-warning">
                    Save these backup codes now.
                  </p>
                  <button
                    type="button"
                    onClick={copyBackupCodes}
                    className="inline-flex h-8 items-center gap-1.5 rounded-md border border-warning/30 px-2.5 text-xs text-warning hover:bg-warning/10"
                  >
                    <Copy className="size-3.5" />
                    Copy
                  </button>
                </div>
                <div className="mt-3 grid grid-cols-2 gap-2 font-mono text-xs text-warning sm:grid-cols-3">
                  {backupCodes.map((backupCode) => (
                    <span key={backupCode}>{backupCode}</span>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {step === "enabled" && (
        <div className="mt-5 max-w-md">
          <p className="flex items-center gap-2 text-sm text-success">
            <Check className="size-4" />
            Authenticator verification is required for future sign-ins.
          </p>
          <label className="mt-4 flex flex-col gap-1.5">
            <span className="text-sm font-medium text-foreground">
              Password required to disable
            </span>
            <input
              type="password"
              value={disablePassword}
              onChange={(e) => setDisablePassword(e.target.value)}
              autoComplete="current-password"
              className="h-11 rounded-md border border-border bg-background/60 px-4 text-sm text-foreground outline-none focus:border-brand/60 focus:ring-2 focus:ring-brand/30"
            />
          </label>
          <button
            type="button"
            onClick={disableTwoFactor}
            disabled={pending || !disablePassword}
            className="mt-4 inline-flex h-10 cursor-pointer items-center gap-2 rounded-md border border-destructive/30 bg-destructive/10 px-4 text-sm font-semibold text-destructive transition-colors hover:bg-destructive/15 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {pending ? <Loader2 className="size-4 animate-spin" /> : "Disable 2FA"}
          </button>
        </div>
      )}

      {message && (
        <p
          aria-live="polite"
          className={cn(
            "mt-4 text-sm",
            message.kind === "success" ? "text-success" : "text-destructive",
          )}
        >
          {message.text}
        </p>
      )}
    </section>
  );
}
