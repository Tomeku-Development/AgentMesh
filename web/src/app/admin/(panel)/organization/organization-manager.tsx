"use client";

import { useEffect, useState } from "react";
import { Building2, Check, Loader2 } from "lucide-react";

type OrganizationRow = {
  id: string;
  name: string;
  slug: string;
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

function slugify(value: string) {
  return value
    .toLowerCase()
    .trim()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .slice(0, 80);
}

const fmt = new Intl.DateTimeFormat("en-US", { dateStyle: "medium" });

export function OrganizationManager() {
  const [organizations, setOrganizations] = useState<OrganizationRow[]>([]);
  const [activeOrganizationId, setActiveOrganizationId] = useState<string | null>(null);
  const [name, setName] = useState("AgentMesh HQ");
  const [pending, setPending] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function fetchOrganizations() {
    const [list, active] = await Promise.all([
      authFetch<OrganizationRow[]>("/organization/list"),
      authFetch<(OrganizationRow & { members?: unknown[] }) | null>(
        "/organization/get-full-organization",
      ).catch(() => null),
    ]);
    return { list, activeId: active?.id ?? null };
  }

  async function loadOrganizations() {
    const data = await fetchOrganizations();
    setOrganizations(data.list);
    setActiveOrganizationId(data.activeId);
  }

  useEffect(() => {
    let canceled = false;
    async function loadInitialOrganizations() {
      try {
        const data = await fetchOrganizations();
        if (!canceled) {
          setOrganizations(data.list);
          setActiveOrganizationId(data.activeId);
        }
      } catch (err) {
        if (!canceled) {
          setError(
            err instanceof Error ? err.message : "Could not load organizations.",
          );
        }
      }
    }
    loadInitialOrganizations();
    return () => {
      canceled = true;
    };
  }, []);

  async function createOrganization() {
    setPending(true);
    setError(null);
    setMessage(null);
    try {
      const slug = slugify(name);
      await authFetch("/organization/create", {
        method: "POST",
        body: JSON.stringify({
          name: name.trim(),
          slug,
          keepCurrentActiveOrganization: false,
        }),
      });
      setMessage("Organization created.");
      await loadOrganizations();
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Could not create organization.",
      );
    } finally {
      setPending(false);
    }
  }

  async function setActive(organizationId: string) {
    setPending(true);
    setError(null);
    setMessage(null);
    try {
      await authFetch("/organization/set-active", {
        method: "POST",
        body: JSON.stringify({ organizationId }),
      });
      setActiveOrganizationId(organizationId);
      setMessage("Active organization updated.");
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Could not set active organization.",
      );
    } finally {
      setPending(false);
    }
  }

  return (
    <div className="space-y-6">
      <section className="rounded-xl border border-border bg-card p-5">
        <div className="flex items-center gap-2 border-b border-border pb-4">
          <Building2 className="size-4 text-brand" />
          <h2 className="font-heading text-sm font-semibold text-foreground">
            Create organization
          </h2>
        </div>
        <div className="mt-5 flex flex-col gap-3 sm:flex-row">
          <input
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="h-10 flex-1 rounded-md border border-border bg-background/60 px-3 text-sm text-foreground outline-none focus:border-brand/60 focus:ring-2 focus:ring-brand/30"
          />
          <button
            type="button"
            onClick={createOrganization}
            disabled={pending || !slugify(name)}
            className="inline-flex h-10 cursor-pointer items-center justify-center gap-2 rounded-md bg-brand px-4 text-sm font-semibold text-primary-foreground transition-all hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {pending ? <Loader2 className="size-4 animate-spin" /> : "Create"}
          </button>
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

      <section className="overflow-hidden rounded-xl border border-border bg-card">
        <div className="border-b border-border px-5 py-4">
          <h2 className="font-heading text-sm font-semibold text-foreground">
            Organizations
          </h2>
        </div>
        {organizations.length === 0 ? (
          <p className="px-5 py-10 text-center text-sm text-muted-foreground">
            No organizations yet.
          </p>
        ) : (
          <div className="divide-y divide-border">
            {organizations.map((organization) => {
              const active = organization.id === activeOrganizationId;
              return (
                <div
                  key={organization.id}
                  className="grid grid-cols-1 gap-3 px-5 py-4 sm:grid-cols-[1fr_auto] sm:items-center"
                >
                  <div className="min-w-0">
                    <p className="truncate text-sm font-medium text-foreground">
                      {organization.name}
                    </p>
                    <p className="truncate text-xs text-muted-foreground">
                      /{organization.slug} · created{" "}
                      {fmt.format(new Date(organization.createdAt))}
                    </p>
                  </div>
                  <button
                    type="button"
                    onClick={() => setActive(organization.id)}
                    disabled={pending || active}
                    className="inline-flex h-9 items-center justify-center gap-2 rounded-md border border-border px-3 text-xs font-semibold text-muted-foreground transition-colors hover:bg-secondary hover:text-foreground disabled:opacity-60"
                  >
                    {active && <Check className="size-3.5 text-success" />}
                    {active ? "Active" : "Set active"}
                  </button>
                </div>
              );
            })}
          </div>
        )}
      </section>
    </div>
  );
}
