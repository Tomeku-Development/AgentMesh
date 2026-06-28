import Link from "next/link";
import {
  ArrowDownToLine,
  CheckCircle2,
  CircleAlert,
  Clock3,
  CreditCard,
  ExternalLink,
  Search,
  TrendingUp,
  XCircle,
  type LucideIcon,
} from "lucide-react";
import { getPaymentTransactions } from "@/lib/data/admin";
import { getPaymentProviderStatus } from "@/lib/payments";
import { formatNumber } from "@/lib/format";
import { cn } from "@/lib/utils";

export const dynamic = "force-dynamic";

type SearchParams = {
  provider?: string;
  status?: string;
  q?: string;
};

type PageProps = {
  searchParams: Promise<SearchParams>;
};

const fmt = new Intl.DateTimeFormat("en-US", {
  dateStyle: "medium",
  timeStyle: "short",
});

const statusGroups = {
  paid: ["paid", "completed", "checkout.session.completed", "succeeded"],
  pending: ["pending", "checkout_created", "invoice_created", "open"],
  failed: ["failed", "expired", "voided", "canceled", "cancelled"],
};

function money(amount: number, currency: string) {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: currency || "USD",
  }).format(amount / 100);
}

function statusKind(status: string): keyof typeof statusGroups | "other" {
  const normalized = status.toLowerCase();
  if (statusGroups.paid.includes(normalized)) return "paid";
  if (statusGroups.pending.includes(normalized)) return "pending";
  if (statusGroups.failed.includes(normalized)) return "failed";
  return "other";
}

function StatusBadge({ status }: { status: string }) {
  const kind = statusKind(status);
  const Icon: LucideIcon =
    kind === "paid"
      ? CheckCircle2
      : kind === "failed"
        ? XCircle
        : kind === "pending"
          ? Clock3
          : CircleAlert;
  return (
    <span
      className={cn(
        "inline-flex w-fit items-center gap-1.5 rounded-full px-2.5 py-1 text-[11px] font-semibold uppercase tracking-wider",
        kind === "paid" && "bg-success/15 text-success",
        kind === "pending" && "bg-warning/15 text-warning",
        kind === "failed" && "bg-destructive/15 text-destructive",
        kind === "other" && "bg-secondary text-muted-foreground",
      )}
    >
      <Icon className="size-3" />
      {status}
    </span>
  );
}

function matchesSearch(
  transaction: Awaited<ReturnType<typeof getPaymentTransactions>>[number],
  q: string,
) {
  if (!q) return true;
  const haystack = [
    transaction.provider,
    transaction.providerTransactionId,
    transaction.plan,
    transaction.currency,
    transaction.status,
    transaction.customerEmail,
  ]
    .join(" ")
    .toLowerCase();
  return haystack.includes(q.toLowerCase());
}

export default async function AdminSalesPage({ searchParams }: PageProps) {
  const params = await searchParams;
  const providerFilter = params.provider ?? "all";
  const statusFilter = params.status ?? "all";
  const q = (params.q ?? "").trim();

  const transactions = await getPaymentTransactions(500);
  const providerStatus = getPaymentProviderStatus();
  const filtered = transactions.filter((transaction) => {
    const providerMatch =
      providerFilter === "all" || transaction.provider === providerFilter;
    const statusMatch =
      statusFilter === "all" || statusKind(transaction.status) === statusFilter;
    return providerMatch && statusMatch && matchesSearch(transaction, q);
  });

  const paid = transactions.filter((item) => statusKind(item.status) === "paid");
  const pending = transactions.filter(
    (item) => statusKind(item.status) === "pending",
  );
  const failed = transactions.filter(
    (item) => statusKind(item.status) === "failed",
  );
  const gross = paid.reduce((sum, item) => sum + item.amount, 0);
  const pipeline = pending.reduce((sum, item) => sum + item.amount, 0);
  const averageOrder = paid.length ? gross / paid.length : 0;
  const conversionRate = transactions.length
    ? Math.round((paid.length / transactions.length) * 100)
    : 0;

  const providerCounts = providerStatus.map((provider) => ({
    ...provider,
    count: transactions.filter((item) => item.provider === provider.provider).length,
    paid: transactions
      .filter(
        (item) =>
          item.provider === provider.provider && statusKind(item.status) === "paid",
      )
      .reduce((sum, item) => sum + item.amount, 0),
  }));

  return (
    <div className="mx-auto max-w-7xl">
      <header className="mb-8 flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="font-heading text-2xl font-bold text-foreground">
            Sales & Payments
          </h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Transaction monitoring, gateway readiness, pipeline, and exports
            across Xendit, Stripe, and Polar.
          </p>
        </div>
        <Link
          href="/api/admin/export/payments"
          className="inline-flex h-10 items-center gap-2 rounded-md border border-border px-3 text-sm font-semibold text-muted-foreground transition-colors hover:bg-secondary hover:text-foreground"
        >
          <ArrowDownToLine className="size-4" />
          Export CSV
        </Link>
      </header>

      <div className="grid grid-cols-2 gap-4 xl:grid-cols-5">
        {[
          {
            label: "Gross sales",
            value: money(gross, "USD"),
            caption: `${formatNumber(paid.length)} paid`,
            icon: TrendingUp,
          },
          {
            label: "Pipeline",
            value: money(pipeline, "USD"),
            caption: `${formatNumber(pending.length)} pending`,
            icon: Clock3,
          },
          {
            label: "Attempts",
            value: formatNumber(transactions.length),
            caption: `${formatNumber(filtered.length)} visible`,
            icon: CreditCard,
          },
          {
            label: "Conversion",
            value: `${conversionRate}%`,
            caption: `${formatNumber(failed.length)} failed`,
            icon: CheckCircle2,
          },
          {
            label: "Avg order",
            value: money(averageOrder, "USD"),
            caption: "Paid only",
            icon: TrendingUp,
          },
        ].map((kpi) => {
          const Icon = kpi.icon;
          return (
            <div key={kpi.label} className="rounded-xl border border-border bg-card p-4">
              <div className="flex items-center gap-2 text-muted-foreground">
                <Icon className="size-4 text-brand" />
                <span className="truncate text-xs font-medium">{kpi.label}</span>
              </div>
              <p className="mt-3 font-heading text-2xl font-bold tabular-nums text-foreground">
                {kpi.value}
              </p>
              <p className="mt-1 text-[11px] text-muted-foreground">
                {kpi.caption}
              </p>
            </div>
          );
        })}
      </div>

      <div className="mt-6 grid grid-cols-1 gap-6 xl:grid-cols-[1fr_360px]">
        <section className="overflow-hidden rounded-xl border border-border bg-card">
          <div className="border-b border-border px-5 py-4">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <h2 className="font-heading text-sm font-semibold text-foreground">
                  Transactions
                </h2>
                <p className="mt-1 text-xs text-muted-foreground">
                  Filter by provider, status, email, transaction ID, or plan.
                </p>
              </div>
              <form className="flex flex-wrap items-center gap-2">
                <div className="relative">
                  <Search className="pointer-events-none absolute left-3 top-1/2 size-3.5 -translate-y-1/2 text-muted-foreground" />
                  <input
                    name="q"
                    defaultValue={q}
                    placeholder="Search"
                    className="h-9 w-48 rounded-md border border-border bg-background/60 pl-8 pr-3 text-sm text-foreground outline-none focus:border-brand/60 focus:ring-2 focus:ring-brand/30"
                  />
                </div>
                <select
                  name="provider"
                  defaultValue={providerFilter}
                  className="h-9 rounded-md border border-border bg-background/60 px-2 text-sm text-foreground outline-none focus:border-brand/60 focus:ring-2 focus:ring-brand/30"
                >
                  <option value="all">All providers</option>
                  <option value="xendit">Xendit</option>
                  <option value="stripe">Stripe</option>
                  <option value="polar">Polar</option>
                </select>
                <select
                  name="status"
                  defaultValue={statusFilter}
                  className="h-9 rounded-md border border-border bg-background/60 px-2 text-sm text-foreground outline-none focus:border-brand/60 focus:ring-2 focus:ring-brand/30"
                >
                  <option value="all">All statuses</option>
                  <option value="paid">Paid</option>
                  <option value="pending">Pending</option>
                  <option value="failed">Failed</option>
                  <option value="other">Other</option>
                </select>
                <button
                  type="submit"
                  className="h-9 rounded-md bg-brand px-3 text-sm font-semibold text-primary-foreground transition-all hover:brightness-110"
                >
                  Apply
                </button>
              </form>
            </div>
          </div>

          {filtered.length === 0 ? (
            <p className="px-5 py-12 text-center text-sm text-muted-foreground">
              No matching transactions.
            </p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full min-w-[920px] text-left text-sm">
                <thead className="border-b border-border bg-secondary/40 text-[11px] uppercase tracking-wider text-muted-foreground">
                  <tr>
                    <th className="px-5 py-3 font-semibold">Customer</th>
                    <th className="px-5 py-3 font-semibold">Provider</th>
                    <th className="px-5 py-3 font-semibold">Status</th>
                    <th className="px-5 py-3 font-semibold">Amount</th>
                    <th className="px-5 py-3 font-semibold">Created</th>
                    <th className="px-5 py-3 font-semibold">Updated</th>
                    <th className="px-5 py-3 text-right font-semibold">Link</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {filtered.map((item) => (
                    <tr key={item.id} className="align-top">
                      <td className="px-5 py-4">
                        <p className="max-w-[220px] truncate font-medium text-foreground">
                          {item.customerEmail ?? "No email"}
                        </p>
                        <p className="mt-1 max-w-[260px] truncate font-mono text-xs text-muted-foreground">
                          {item.providerTransactionId ?? `local-${item.id}`}
                        </p>
                      </td>
                      <td className="px-5 py-4">
                        <p className="capitalize text-foreground">{item.provider}</p>
                        <p className="mt-1 text-xs text-muted-foreground">
                          {item.plan} · {item.currency}
                        </p>
                      </td>
                      <td className="px-5 py-4">
                        <StatusBadge status={item.status} />
                      </td>
                      <td className="px-5 py-4 font-medium tabular-nums text-foreground">
                        {money(item.amount, item.currency)}
                      </td>
                      <td className="px-5 py-4 text-xs text-muted-foreground">
                        {fmt.format(new Date(item.createdAt))}
                      </td>
                      <td className="px-5 py-4 text-xs text-muted-foreground">
                        {fmt.format(new Date(item.updatedAt))}
                      </td>
                      <td className="px-5 py-4 text-right">
                        {item.checkoutUrl ? (
                          <a
                            href={item.checkoutUrl}
                            target="_blank"
                            rel="noreferrer"
                            className="inline-flex size-8 items-center justify-center rounded-md border border-border text-muted-foreground transition-colors hover:bg-secondary hover:text-foreground"
                            title="Open checkout"
                          >
                            <ExternalLink className="size-3.5" />
                          </a>
                        ) : (
                          <span className="text-xs text-muted-foreground">None</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>

        <aside className="space-y-6">
          <section className="rounded-xl border border-border bg-card">
            <div className="border-b border-border px-5 py-4">
              <h2 className="font-heading text-sm font-semibold text-foreground">
                Gateway health
              </h2>
            </div>
            <div className="divide-y divide-border">
              {providerCounts.map((provider) => (
                <div key={provider.provider} className="px-5 py-4">
                  <div className="flex items-center justify-between gap-3">
                    <div className="flex items-center gap-3">
                      <span className="inline-flex size-9 items-center justify-center rounded-full bg-secondary text-brand">
                        <CreditCard className="size-4" />
                      </span>
                      <div>
                        <p className="text-sm font-medium text-foreground">
                          {provider.label}
                        </p>
                        <p className="text-xs text-muted-foreground">
                          {provider.count} transaction{provider.count === 1 ? "" : "s"}
                        </p>
                      </div>
                    </div>
                    <span
                      className={cn(
                        "inline-flex items-center gap-1.5 text-xs font-semibold",
                        provider.configured ? "text-success" : "text-warning",
                      )}
                    >
                      {provider.configured ? (
                        <CheckCircle2 className="size-3.5" />
                      ) : (
                        <CircleAlert className="size-3.5" />
                      )}
                      {provider.configured ? "Ready" : "Needs env"}
                    </span>
                  </div>
                  <div className="mt-3 h-2 overflow-hidden rounded-full bg-secondary">
                    <div
                      className="h-full rounded-full bg-brand"
                      style={{
                        width: `${transactions.length ? Math.round((provider.count / transactions.length) * 100) : 0}%`,
                      }}
                    />
                  </div>
                  <p className="mt-2 text-xs text-muted-foreground">
                    Paid volume {money(provider.paid, "USD")}
                  </p>
                </div>
              ))}
            </div>
          </section>

          <section className="rounded-xl border border-border bg-card p-5">
            <h2 className="font-heading text-sm font-semibold text-foreground">
              Status mix
            </h2>
            <div className="mt-4 grid grid-cols-3 gap-3">
              {[
                ["Paid", paid.length, "text-success"],
                ["Pending", pending.length, "text-warning"],
                ["Failed", failed.length, "text-destructive"],
              ].map(([label, value, color]) => (
                <div key={label} className="rounded-lg border border-border p-3">
                  <p className="text-xs text-muted-foreground">{label}</p>
                  <p className={cn("mt-2 text-lg font-bold", color)}>
                    {value}
                  </p>
                </div>
              ))}
            </div>
          </section>
        </aside>
      </div>
    </div>
  );
}
