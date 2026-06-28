import "server-only";
import { getContactSubmissions, getSubscribers } from "@/lib/data/admin";

export type AnalyticsProviderStatus = {
  name: "GA4" | "PostHog";
  configured: boolean;
  detail: string;
};

export type AnalyticsSummary = {
  subscribers: number;
  messages: number;
  conversions: number;
  conversionRate: number | null;
  providers: AnalyticsProviderStatus[];
  recentLeadEvents: LeadEvent[];
  leadSeries: number[];
};

export type LeadEvent = {
  kind: "newsletter_signup_completed" | "contact_message_sent";
  label: string;
  at: Date;
};

const SERIES_DAYS = 14;

function dayKey(date: Date) {
  return date.toISOString().slice(0, 10);
}

export async function getAnalyticsSummary(): Promise<AnalyticsSummary> {
  const [subscribers, messages] = await Promise.all([
    getSubscribers(),
    getContactSubmissions(),
  ]);

  const allLeadEvents: LeadEvent[] = [
    ...subscribers.map((row) => ({
      kind: "newsletter_signup_completed" as const,
      label: row.email,
      at: new Date(row.createdAt),
    })),
    ...messages.map((row) => ({
      kind: "contact_message_sent" as const,
      label: row.company ? `${row.name} · ${row.company}` : row.name,
      at: new Date(row.createdAt),
    })),
  ].sort((a, b) => b.at.getTime() - a.at.getTime());

  const days = Array.from({ length: SERIES_DAYS }, (_, i) => {
    const date = new Date();
    date.setUTCHours(0, 0, 0, 0);
    date.setUTCDate(date.getUTCDate() - (SERIES_DAYS - 1 - i));
    return dayKey(date);
  });
  const counts = new Map(days.map((day) => [day, 0]));

  for (const event of allLeadEvents) {
    const key = dayKey(event.at);
    if (counts.has(key)) counts.set(key, (counts.get(key) ?? 0) + 1);
  }

  const conversions = subscribers.length + messages.length;

  return {
    subscribers: subscribers.length,
    messages: messages.length,
    conversions,
    conversionRate: null,
    providers: [
      {
        name: "GA4",
        configured: Boolean(process.env.NEXT_PUBLIC_GA_MEASUREMENT_ID),
        detail: process.env.NEXT_PUBLIC_GA_MEASUREMENT_ID || "Not configured",
      },
      {
        name: "PostHog",
        configured: Boolean(process.env.NEXT_PUBLIC_POSTHOG_KEY),
        detail: process.env.NEXT_PUBLIC_POSTHOG_HOST || "Not configured",
      },
    ],
    recentLeadEvents: allLeadEvents.slice(0, 8),
    leadSeries: days.map((day) => counts.get(day) ?? 0),
  };
}
