"use client";

import { useEffect, useState } from "react";
import { Fingerprint, KeyRound, Loader2, Trash2 } from "lucide-react";
import { authClient } from "@/lib/auth-client";

type PasskeyRow = {
  id: string;
  name?: string | null;
  deviceType: string;
  backedUp: boolean;
  createdAt: string | Date;
};

async function authFetch<T>(
  path: string,
  init: RequestInit = {},
): Promise<T> {
  const res = await fetch(`/api/auth${path}`, {
    ...init,
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...(init.headers ?? {}),
    },
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    throw new Error(data?.message || data?.error || "Request failed.");
  }
  return data as T;
}

const fmt = new Intl.DateTimeFormat("en-US", { dateStyle: "medium" });

export function PasskeyCard() {
  const [passkeys, setPasskeys] = useState<PasskeyRow[]>([]);
  const [name, setName] = useState("Admin passkey");
  const [pending, setPending] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function fetchPasskeys() {
    const data = await authFetch<PasskeyRow[]>("/passkey/list-user-passkeys");
    return data;
  }

  async function loadPasskeys() {
    setPasskeys(await fetchPasskeys());
  }

  useEffect(() => {
    let canceled = false;
    async function loadInitialPasskeys() {
      try {
        const data = await fetchPasskeys();
        if (!canceled) setPasskeys(data);
      } catch (err) {
        if (!canceled) {
          setError(
            err instanceof Error ? err.message : "Could not load passkeys.",
          );
        }
      }
    }
    loadInitialPasskeys();
    return () => {
      canceled = true;
    };
  }, []);

  async function addPasskey() {
    setPending(true);
    setError(null);
    setMessage(null);
    try {
      const result = await authClient.passkey.addPasskey({
        name: name.trim() || "Admin passkey",
      });
      if (result.error) {
        setError(result.error.message ?? "Could not add passkey.");
        return;
      }
      setMessage("Passkey added.");
      await loadPasskeys();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not add passkey.");
    } finally {
      setPending(false);
    }
  }

  async function deletePasskey(id: string) {
    setPending(true);
    setError(null);
    setMessage(null);
    try {
      await authFetch("/passkey/delete-passkey", {
        method: "POST",
        body: JSON.stringify({ id }),
      });
      setMessage("Passkey removed.");
      await loadPasskeys();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not remove passkey.");
    } finally {
      setPending(false);
    }
  }

  return (
    <section className="rounded-xl border border-border bg-card p-5">
      <div className="flex flex-wrap items-start justify-between gap-4 border-b border-border pb-4">
        <div>
          <h2 className="font-heading text-sm font-semibold text-foreground">
            Passkeys
          </h2>
          <p className="mt-1 text-xs text-muted-foreground">
            Sign in with Touch ID, Face ID, Windows Hello, or a security key.
          </p>
        </div>
        <Fingerprint className="size-5 text-brand" />
      </div>

      <div className="mt-5 flex flex-col gap-3 sm:flex-row">
        <input
          value={name}
          onChange={(e) => setName(e.target.value)}
          className="h-10 flex-1 rounded-md border border-border bg-background/60 px-3 text-sm text-foreground outline-none focus:border-brand/60 focus:ring-2 focus:ring-brand/30"
        />
        <button
          type="button"
          onClick={addPasskey}
          disabled={pending}
          className="inline-flex h-10 cursor-pointer items-center justify-center gap-2 rounded-md bg-brand px-4 text-sm font-semibold text-primary-foreground transition-all hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {pending ? <Loader2 className="size-4 animate-spin" /> : <KeyRound className="size-4" />}
          Add passkey
        </button>
      </div>

      <div className="mt-5 divide-y divide-border overflow-hidden rounded-lg border border-border">
        {passkeys.length === 0 ? (
          <p className="px-4 py-5 text-sm text-muted-foreground">
            No passkeys registered yet.
          </p>
        ) : (
          passkeys.map((passkey) => (
            <div
              key={passkey.id}
              className="flex flex-wrap items-center justify-between gap-3 px-4 py-3"
            >
              <div>
                <p className="text-sm font-medium text-foreground">
                  {passkey.name || "Unnamed passkey"}
                </p>
                <p className="text-xs text-muted-foreground">
                  {passkey.deviceType} · {passkey.backedUp ? "synced" : "device-bound"} · {fmt.format(new Date(passkey.createdAt))}
                </p>
              </div>
              <button
                type="button"
                onClick={() => deletePasskey(passkey.id)}
                disabled={pending}
                className="inline-flex size-8 items-center justify-center rounded-md border border-border text-muted-foreground transition-colors hover:border-destructive/40 hover:bg-destructive/10 hover:text-destructive disabled:opacity-60"
                title="Remove passkey"
              >
                <Trash2 className="size-3.5" />
              </button>
            </div>
          ))
        )}
      </div>

      {(message || error) && (
        <p
          className={`mt-4 text-sm ${error ? "text-destructive" : "text-success"}`}
          aria-live="polite"
        >
          {error ?? message}
        </p>
      )}
    </section>
  );
}
