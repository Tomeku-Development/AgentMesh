import {
  BarChart3,
  CheckCircle2,
  CircleAlert,
  Mail,
  MessageSquare,
  MousePointerClick,
  UserPlus,
  type LucideIcon,
} from "lucide-react";
import { Sparkline } from "@/components/admin/sparkline";
import { getAnalyticsSummary } from "@/lib/data/analytics";
import { isDatabaseConfigured } from "@/lib/db";
import { formatNumber } from "@/lib/format";
import { cn } from "@/lib/utils";

export const dynamic = "force-dynamic";

const events: Array<{
  event: string;
  description: string;
  trigger: string;
}> = [
  {
    event: "page_viewed",
    description: "Route-level page view",
    trigger: "Route change",
  },
  {
    event: "cta_clicked",
    description: "Meaningful CTA intent",
    trigger: "Annotated CTA click",
  },
  {
    event: "form_started",
    description: "Lead form received first focus",
    trigger: "First form field focus",
  },
  {
    event: "newsletter_signup_completed",
    description: "Early-access signup succeeded",
    trigger: "Subscribe action success",
  },
  {
    event: "contact_message_sent",
    description: "Contact request succeeded",
    trigger: "Contact action success",
  },
];

const fmt = new Intl.DateTimeFormat("en-US", {
  dateStyle: "medium",
  timeStyle: "short",
});

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

export default async function AdminAnalyticsPage() {
  const summary = await getAnalyticsSummary();

  const kpis: Array<{
    label: string;
    value: string;
    caption: string;
    icon: LucideIcon;
  }> = [
    {
      label: "Lead conversions",
      value: formatNumber(summary.conversions),
      caption: "Newsletter + contact",
      icon: UserPlus,
    },
    {
      label: "Subscribers",
      value: formatNumber(summary.subscribers),
      caption: "Early access",
      icon: Mail,
    },
    {
      label: "Messages",
      value: formatNumber(summary.messages),
      caption: "High-intent leads",
      icon: MessageSquare,
    },
    {
      label: "Tracked events",
      value: formatNumber(events.length),
      caption: "Current event model",
      icon: BarChart3,
    },
  ];

  return (
    <div className="mx-auto max-w-6xl">
      <header className="mb-8">
        <div>
          <h1 className="font-heading text-2xl font-bold text-foreground">
            Analytics
          </h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Product and marketing signals from the public site. Provider keys
            are optional.
          </p>
        </div>
      </header>

      {!isDatabaseConfigured && (
        <div className="mb-6 rounded-xl border border-warning/30 bg-warning/10 p-4 text-sm text-warning">
          Database not configured. Lead conversion cards use fallback/empty
          data until <code>DATABASE_URL</code> is set.
        </div>
      )}

      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        {kpis.map((kpi) => {
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

      <div className="mt-6 grid grid-cols-1 gap-6 lg:grid-cols-3">
        <section className="rounded-xl border border-border bg-card p-5 lg:col-span-2">
          <div className="flex items-center justify-between gap-4">
            <div>
              <h2 className="font-heading text-sm font-semibold text-foreground">
                Lead conversions
              </h2>
              <p className="mt-1 text-xs text-muted-foreground">
                Last 14 days from persisted lead submissions.
              </p>
            </div>
            <span className="rounded-full bg-brand/15 px-2.5 py-1 text-xs font-medium text-brand">
              {formatNumber(summary.conversions)} total
            </span>
          </div>
          <div className="mt-6 h-40">
            <Sparkline
              id="analytics-leads"
              data={summary.leadSeries.length ? summary.leadSeries : [0, 0]}
              width={640}
              height={160}
              className="h-full w-full text-brand"
            />
          </div>
        </section>

        <section className="rounded-xl border border-border bg-card">
          <div className="border-b border-border px-5 py-4">
            <h2 className="font-heading text-sm font-semibold text-foreground">
              Provider setup
            </h2>
          </div>
          <ul className="flex flex-col">
            {summary.providers.map((provider) => (
              <li
                key={provider.name}
                className="flex items-center justify-between gap-3 px-5 py-3"
              >
                <div className="min-w-0">
                  <p className="text-sm font-medium text-foreground">
                    {provider.name}
                  </p>
                  <p className="truncate text-xs text-muted-foreground">
                    {provider.detail}
                  </p>
                </div>
                <span
                  className={cn(
                    "inline-flex shrink-0 items-center gap-1.5 text-xs font-medium",
                    provider.configured ? "text-success" : "text-warning",
                  )}
                >
                  {provider.configured ? (
                    <CheckCircle2 className="size-3.5" />
                  ) : (
                    <CircleAlert className="size-3.5" />
                  )}
                  {provider.configured ? "Live" : "Setup"}
                </span>
              </li>
            ))}
          </ul>
        </section>
      </div>

      <div className="mt-6 grid grid-cols-1 gap-6 lg:grid-cols-2">
        <section className="rounded-xl border border-border bg-card">
          <div className="border-b border-border px-5 py-4">
            <h2 className="font-heading text-sm font-semibold text-foreground">
              Recent lead activity
            </h2>
          </div>
          {summary.recentLeadEvents.length === 0 ? (
            <p className="px-5 py-10 text-center text-sm text-muted-foreground">
              No lead events yet.
            </p>
          ) : (
            <ul className="divide-y divide-border">
              {summary.recentLeadEvents.map((event, i) => {
                const Icon =
                  event.kind === "contact_message_sent" ? MessageSquare : Mail;
                return (
                  <li key={`${event.kind}-${i}`} className="flex items-center gap-3 px-5 py-3">
                    <span className="inline-flex size-8 shrink-0 items-center justify-center rounded-full bg-secondary text-brand">
                      <Icon className="size-4" />
                    </span>
                    <div className="min-w-0 flex-1">
                      <p className="truncate text-sm font-medium text-foreground">
                        {event.kind}
                      </p>
                      <p className="truncate text-xs text-muted-foreground">
                        {event.label} · {fmt.format(event.at)}
                      </p>
                    </div>
                    <span className="shrink-0 text-xs text-muted-foreground">
                      {relativeTime(event.at)}
                    </span>
                  </li>
                );
              })}
            </ul>
          )}
        </section>

        <section className="rounded-xl border border-border bg-card">
          <div className="border-b border-border px-5 py-4">
            <h2 className="font-heading text-sm font-semibold text-foreground">
              Event model
            </h2>
          </div>
          <div className="divide-y divide-border">
            {events.map((event) => (
              <div key={event.event} className="flex gap-3 px-5 py-3">
                <span className="mt-0.5 inline-flex size-7 shrink-0 items-center justify-center rounded-full bg-secondary text-brand">
                  <MousePointerClick className="size-3.5" />
                </span>
                <div>
                  <p className="font-mono text-xs font-semibold text-foreground">
                    {event.event}
                  </p>
                  <p className="mt-1 text-xs leading-relaxed text-muted-foreground">
                    {event.description} · {event.trigger}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </section>
      </div>
    </div>
  );
}
