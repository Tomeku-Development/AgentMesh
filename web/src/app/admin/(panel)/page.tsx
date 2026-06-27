import Link from "next/link";
import {
  Mail,
  MessageSquare,
  Image as ImageIcon,
  Users,
  ArrowLeftRight,
  Coins,
  Database,
  HardDrive,
  Network,
  Boxes,
  UserPlus,
  type LucideIcon,
} from "lucide-react";
import { isDatabaseConfigured } from "@/lib/db";
import { storageInfo } from "@/lib/storage";
import { getAdminCounts, getRecentActivity } from "@/lib/data/admin";
import { getNetworkStats } from "@/lib/data/stats";
import { getHealth, type ServiceStatus } from "@/lib/data/health";
import { formatNumber, formatCompact } from "@/lib/format";
import { Sparkline, seededSeries } from "@/components/admin/sparkline";
import { cn } from "@/lib/utils";

export const dynamic = "force-dynamic";

function relativeTime(date: Date): string {
  const s = Math.floor((Date.now() - date.getTime()) / 1000);
  if (s < 60) return "just now";
  const m = Math.floor(s / 60);
  if (m < 60) return `${m}m ago`;
  const h = Math.floor(m / 60);
  if (h < 24) return `${h}h ago`;
  const d = Math.floor(h / 24);
  return `${d}d ago`;
}

export default async function AdminDashboard() {
  const [counts, activity, stats, health, storage] = await Promise.all([
    getAdminCounts(),
    getRecentActivity(7),
    getNetworkStats(),
    getHealth(),
    Promise.resolve(storageInfo()),
  ]);

  const kpis = [
    { label: "Subscribers", value: formatNumber(counts.subscribers), caption: "All time", icon: Mail, seed: 7 },
    { label: "Messages", value: formatNumber(counts.messages), caption: "All time", icon: MessageSquare, seed: 13 },
    { label: "Media assets", value: formatNumber(counts.media), caption: "Stored", icon: ImageIcon, seed: 21 },
    { label: "Agents online", value: formatNumber(stats.agentsOnline), caption: "Live network", icon: Users, seed: 31 },
    { label: "Transactions", value: formatNumber(stats.transactions), caption: "Live network", icon: ArrowLeftRight, seed: 42 },
    { label: "TVL on Casper", value: `${formatCompact(stats.tvlCspr)}`, caption: "CSPR", icon: Coins, seed: 55 },
  ];

  const services: { name: string; status: ServiceStatus; icon: LucideIcon }[] = [
    { name: "Web / API", status: health.api, icon: Network },
    { name: "Database", status: health.database, icon: Database },
    { name: "Media storage", status: storage.configured ? "operational" : "not_configured", icon: HardDrive },
    { name: "Casper Network", status: health.blockchain, icon: Boxes },
  ];

  const activityIcon: Record<string, LucideIcon> = {
    subscriber: UserPlus,
    message: MessageSquare,
    media: ImageIcon,
  };

  return (
    <div className="mx-auto max-w-6xl">
      {/* Welcome */}
      <div className="mb-8 flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="font-heading text-2xl font-bold text-foreground">
            Welcome back 👋
          </h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Here&apos;s what&apos;s happening across your workspace.
          </p>
        </div>
        <span className="inline-flex items-center gap-2 rounded-lg border border-border bg-card px-3 py-2 text-sm text-foreground">
          <span className="flex size-5 items-center justify-center rounded bg-brand/15 text-[10px] font-bold text-brand">
            AM
          </span>
          {storage.bucket ? "AgentMesh HQ" : "AgentMesh HQ"}
        </span>
      </div>

      {!isDatabaseConfigured && (
        <div className="mb-6 rounded-xl border border-warning/30 bg-warning/10 p-4 text-sm text-warning">
          Database not configured. Set <code>DATABASE_URL</code> for live data.
        </div>
      )}

      {/* KPI cards */}
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-3 xl:grid-cols-6">
        {kpis.map((kpi) => {
          const Icon = kpi.icon;
          return (
            <div
              key={kpi.label}
              className="rounded-xl border border-border bg-card p-4"
            >
              <div className="flex items-center gap-2 text-muted-foreground">
                <Icon className="size-4 text-brand" />
                <span className="truncate text-xs font-medium">{kpi.label}</span>
              </div>
              <p className="mt-3 font-heading text-2xl font-bold tabular-nums text-foreground">
                {kpi.value}
              </p>
              <div className="mt-2 h-9">
                <Sparkline
                  id={String(kpi.seed)}
                  data={seededSeries(kpi.seed)}
                  width={160}
                  height={36}
                  className="h-full w-full text-brand"
                />
              </div>
              <p className="mt-1 text-[11px] text-muted-foreground">
                {kpi.caption}
              </p>
            </div>
          );
        })}
      </div>

      {/* Activity + status */}
      <div className="mt-6 grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Recent activity */}
        <div className="lg:col-span-2 rounded-xl border border-border bg-card">
          <div className="flex items-center justify-between border-b border-border px-5 py-4">
            <h2 className="font-heading text-sm font-semibold text-foreground">
              Recent activity
            </h2>
            <Link
              href="/admin/messages"
              className="text-xs text-brand hover:underline"
            >
              View all
            </Link>
          </div>
          {activity.length === 0 ? (
            <p className="px-5 py-10 text-center text-sm text-muted-foreground">
              No activity yet.
            </p>
          ) : (
            <ul className="divide-y divide-border">
              {activity.map((item, i) => {
                const Icon = activityIcon[item.kind] ?? UserPlus;
                return (
                  <li key={i} className="flex items-center gap-3 px-5 py-3">
                    <span className="inline-flex size-8 shrink-0 items-center justify-center rounded-full bg-secondary text-brand">
                      <Icon className="size-4" />
                    </span>
                    <div className="min-w-0 flex-1">
                      <p className="truncate text-sm font-medium text-foreground">
                        {item.title}
                      </p>
                      <p className="truncate text-xs text-muted-foreground">
                        {item.subtitle}
                      </p>
                    </div>
                    <span className="shrink-0 text-xs text-muted-foreground">
                      {relativeTime(item.at)}
                    </span>
                  </li>
                );
              })}
            </ul>
          )}
        </div>

        {/* System status */}
        <div className="rounded-xl border border-border bg-card">
          <div className="border-b border-border px-5 py-4">
            <h2 className="font-heading text-sm font-semibold text-foreground">
              System status
            </h2>
          </div>
          <ul className="flex flex-col">
            {services.map((s) => {
              const Icon = s.icon;
              const ok = s.status === "operational";
              const setup = s.status === "not_configured";
              return (
                <li
                  key={s.name}
                  className="flex items-center justify-between gap-3 px-5 py-3"
                >
                  <span className="flex items-center gap-2.5 text-sm text-foreground">
                    <Icon className="size-4 text-muted-foreground" />
                    {s.name}
                  </span>
                  <span
                    className={cn(
                      "inline-flex items-center gap-1.5 text-xs font-medium",
                      ok ? "text-success" : setup ? "text-warning" : "text-destructive",
                    )}
                  >
                    <span
                      className={cn(
                        "size-1.5 rounded-full",
                        ok ? "bg-success" : setup ? "bg-warning" : "bg-destructive",
                      )}
                    />
                    {ok ? "Healthy" : setup ? "Setup" : "Down"}
                  </span>
                </li>
              );
            })}
          </ul>
          <div className="border-t border-border px-5 py-3">
            <Link
              href="/status"
              className="text-xs text-brand hover:underline"
            >
              Public status page →
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
