import {
  CheckCircle2,
  CircleAlert,
  Database,
  KeyRound,
  ShieldCheck,
} from "lucide-react";
import { getAdminCounts } from "@/lib/data/admin";
import { isDatabaseConfigured } from "@/lib/db";
import { getPaymentProviderStatus } from "@/lib/payments";
import { cn } from "@/lib/utils";

export const dynamic = "force-dynamic";

type Check = {
  label: string;
  detail: string;
  ok: boolean;
  icon: typeof CheckCircle2;
};

function configured(name: string) {
  return Boolean(process.env[name]);
}

export default async function AdminReportsPage() {
  const counts = await getAdminCounts();
  const providerStatus = getPaymentProviderStatus();
  const checks: Check[] = [
    {
      label: "Database",
      detail: "Required for CMS, leads, sales, API keys, and audit-ready admin data.",
      ok: isDatabaseConfigured,
      icon: Database,
    },
    {
      label: "Auth secret",
      detail: "BETTER_AUTH_SECRET should be set to a long random production secret.",
      ok: configured("BETTER_AUTH_SECRET"),
      icon: ShieldCheck,
    },
    {
      label: "Auth origin",
      detail: "BETTER_AUTH_URL or NEXT_PUBLIC_SITE_URL should match production.",
      ok: configured("BETTER_AUTH_URL") || configured("NEXT_PUBLIC_SITE_URL"),
      icon: KeyRound,
    },
    {
      label: "Xendit",
      detail: "Main checkout gateway for Pro payments.",
      ok: providerStatus.find((p) => p.provider === "xendit")?.configured ?? false,
      icon: KeyRound,
    },
    {
      label: "Stripe",
      detail: "Fallback checkout gateway.",
      ok: providerStatus.find((p) => p.provider === "stripe")?.configured ?? false,
      icon: KeyRound,
    },
    {
      label: "Polar",
      detail: "Alternative checkout gateway for software subscriptions.",
      ok: providerStatus.find((p) => p.provider === "polar")?.configured ?? false,
      icon: KeyRound,
    },
    {
      label: "Analytics",
      detail: "GA4 or PostHog should be configured before launch.",
      ok: configured("NEXT_PUBLIC_GA_MEASUREMENT_ID") || configured("NEXT_PUBLIC_POSTHOG_KEY"),
      icon: CheckCircle2,
    },
    {
      label: "Media storage",
      detail: "S3/R2 is needed for production media uploads.",
      ok:
        configured("S3_BUCKET") &&
        configured("S3_ACCESS_KEY_ID") &&
        configured("S3_SECRET_ACCESS_KEY") &&
        configured("S3_PUBLIC_BASE_URL"),
      icon: Database,
    },
  ];

  const ready = checks.filter((check) => check.ok).length;

  return (
    <div className="mx-auto max-w-6xl">
      <header className="mb-8">
        <h1 className="font-heading text-2xl font-bold text-foreground">
          Reports & Readiness
        </h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Operational checks, sales readiness, and launch-blocking setup items.
        </p>
      </header>

      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <div className="rounded-xl border border-border bg-card p-4">
          <p className="text-xs text-muted-foreground">Readiness</p>
          <p className="mt-3 font-heading text-2xl font-bold text-foreground">
            {ready}/{checks.length}
          </p>
        </div>
        <div className="rounded-xl border border-border bg-card p-4">
          <p className="text-xs text-muted-foreground">Subscribers</p>
          <p className="mt-3 font-heading text-2xl font-bold text-foreground">
            {counts.subscribers}
          </p>
        </div>
        <div className="rounded-xl border border-border bg-card p-4">
          <p className="text-xs text-muted-foreground">Sales messages</p>
          <p className="mt-3 font-heading text-2xl font-bold text-foreground">
            {counts.messages}
          </p>
        </div>
        <div className="rounded-xl border border-border bg-card p-4">
          <p className="text-xs text-muted-foreground">Checkout attempts</p>
          <p className="mt-3 font-heading text-2xl font-bold text-foreground">
            {counts.payments}
          </p>
        </div>
      </div>

      <section className="mt-6 overflow-hidden rounded-xl border border-border bg-card">
        <div className="border-b border-border px-5 py-4">
          <h2 className="font-heading text-sm font-semibold text-foreground">
            Launch checks
          </h2>
        </div>
        <div className="divide-y divide-border">
          {checks.map((check) => {
            const Icon = check.icon;
            return (
              <div
                key={check.label}
                className="flex flex-wrap items-center justify-between gap-4 px-5 py-4"
              >
                <div className="flex min-w-0 items-start gap-3">
                  <span className="inline-flex size-9 shrink-0 items-center justify-center rounded-full bg-secondary text-brand">
                    <Icon className="size-4" />
                  </span>
                  <div className="min-w-0">
                    <p className="text-sm font-medium text-foreground">
                      {check.label}
                    </p>
                    <p className="mt-1 text-xs text-muted-foreground">
                      {check.detail}
                    </p>
                  </div>
                </div>
                <span
                  className={cn(
                    "inline-flex items-center gap-1.5 text-xs font-semibold",
                    check.ok ? "text-success" : "text-warning",
                  )}
                >
                  {check.ok ? (
                    <CheckCircle2 className="size-3.5" />
                  ) : (
                    <CircleAlert className="size-3.5" />
                  )}
                  {check.ok ? "Ready" : "Needs setup"}
                </span>
              </div>
            );
          })}
        </div>
      </section>
    </div>
  );
}
