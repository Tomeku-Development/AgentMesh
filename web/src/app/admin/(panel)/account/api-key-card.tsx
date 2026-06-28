"use client";

import { useEffect, useState } from "react";
import { Copy, Key, Loader2, Trash2 } from "lucide-react";

type ApiKeyRow = {
  id: string;
  name: string | null;
  start: string | null;
  enabled: boolean;
  rateLimitMax: number | null;
  rateLimitTimeWindow: number | null;
  requestCount: number;
  expiresAt: string | Date | null;
  lastRequest: string | Date | null;
  createdAt: string | Date;
};

type ListResponse = {
  apiKeys: ApiKeyRow[];
  total: number;
};

type CreateResponse = ApiKeyRow & {
  key: string;
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

const fmt = new Intl.DateTimeFormat("en-US", {
  dateStyle: "medium",
  timeStyle: "short",
});

function formatDate(value: string | Date | null) {
  return value ? fmt.format(new Date(value)) : "Never";
}

export function ApiKeyCard() {
  const [apiKeys, setApiKeys] = useState<ApiKeyRow[]>([]);
  const [name, setName] = useState("Admin automation");
  const [newKey, setNewKey] = useState<string | null>(null);
  const [pending, setPending] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function fetchKeys() {
    const data = await authFetch<ListResponse>("/api-key/list");
    return data.apiKeys;
  }

  async function loadKeys() {
    setApiKeys(await fetchKeys());
  }

  useEffect(() => {
    let canceled = false;
    async function loadInitialKeys() {
      try {
        const data = await fetchKeys();
        if (!canceled) setApiKeys(data);
      } catch (err) {
        if (!canceled) {
          setError(
            err instanceof Error ? err.message : "Could not load API keys.",
          );
        }
      }
    }
    loadInitialKeys();
    return () => {
      canceled = true;
    };
  }, []);

  async function createKey() {
    setPending(true);
    setError(null);
    setMessage(null);
    setNewKey(null);
    try {
      const data = await authFetch<CreateResponse>("/api-key/create", {
        method: "POST",
        body: JSON.stringify({
          name: name.trim() || "Admin automation",
          metadata: { scope: "admin" },
        }),
      });
      setNewKey(data.key);
      setMessage("API key created. Copy it now; it is only shown once.");
      await loadKeys();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not create API key.");
    } finally {
      setPending(false);
    }
  }

  async function deleteKey(keyId: string) {
    setPending(true);
    setError(null);
    setMessage(null);
    try {
      await authFetch("/api-key/delete", {
        method: "POST",
        body: JSON.stringify({ keyId }),
      });
      setMessage("API key deleted.");
      await loadKeys();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not delete API key.");
    } finally {
      setPending(false);
    }
  }

  async function copyKey() {
    if (!newKey) return;
    await navigator.clipboard.writeText(newKey);
    setMessage("API key copied.");
  }

  return (
    <section className="rounded-xl border border-border bg-card p-5">
      <div className="flex flex-wrap items-start justify-between gap-4 border-b border-border pb-4">
        <div>
          <h2 className="font-heading text-sm font-semibold text-foreground">
            API keys
          </h2>
          <p className="mt-1 text-xs text-muted-foreground">
            Create local AgentMesh API keys for scripts and integrations.
          </p>
        </div>
        <Key className="size-5 text-brand" />
      </div>

      <div className="mt-5 flex flex-col gap-3 sm:flex-row">
        <input
          value={name}
          onChange={(e) => setName(e.target.value)}
          className="h-10 flex-1 rounded-md border border-border bg-background/60 px-3 text-sm text-foreground outline-none focus:border-brand/60 focus:ring-2 focus:ring-brand/30"
        />
        <button
          type="button"
          onClick={createKey}
          disabled={pending}
          className="inline-flex h-10 cursor-pointer items-center justify-center gap-2 rounded-md bg-brand px-4 text-sm font-semibold text-primary-foreground transition-all hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {pending ? <Loader2 className="size-4 animate-spin" /> : <Key className="size-4" />}
          Create key
        </button>
      </div>

      {newKey && (
        <div className="mt-4 rounded-lg border border-warning/30 bg-warning/10 p-4">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <p className="text-sm font-medium text-warning">
              Copy this key now. It will not be shown again.
            </p>
            <button
              type="button"
              onClick={copyKey}
              className="inline-flex h-8 items-center gap-1.5 rounded-md border border-warning/30 px-2.5 text-xs text-warning hover:bg-warning/10"
            >
              <Copy className="size-3.5" />
              Copy
            </button>
          </div>
          <p className="mt-3 break-all rounded-md bg-background/60 p-3 font-mono text-xs text-warning">
            {newKey}
          </p>
        </div>
      )}

      <div className="mt-5 divide-y divide-border overflow-hidden rounded-lg border border-border">
        {apiKeys.length === 0 ? (
          <p className="px-4 py-5 text-sm text-muted-foreground">
            No API keys created yet.
          </p>
        ) : (
          apiKeys.map((apiKey) => (
            <div
              key={apiKey.id}
              className="grid grid-cols-1 gap-3 px-4 py-3 sm:grid-cols-[1fr_auto] sm:items-center"
            >
              <div className="min-w-0">
                <p className="truncate text-sm font-medium text-foreground">
                  {apiKey.name || "Unnamed key"}
                </p>
                <p className="truncate text-xs text-muted-foreground">
                  {apiKey.start ?? "hidden"} · {apiKey.enabled ? "enabled" : "disabled"} · expires {formatDate(apiKey.expiresAt)}
                </p>
                <p className="mt-1 text-xs text-muted-foreground">
                  {apiKey.requestCount} requests · last used {formatDate(apiKey.lastRequest)}
                </p>
              </div>
              <button
                type="button"
                onClick={() => deleteKey(apiKey.id)}
                disabled={pending}
                className="inline-flex size-8 items-center justify-center rounded-md border border-border text-muted-foreground transition-colors hover:border-destructive/40 hover:bg-destructive/10 hover:text-destructive disabled:opacity-60"
                title="Delete API key"
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
