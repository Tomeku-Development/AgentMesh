"use client";

export type AnalyticsEventName =
  | "page_viewed"
  | "cta_clicked"
  | "form_started"
  | "newsletter_signup_completed"
  | "newsletter_signup_failed"
  | "contact_message_sent"
  | "contact_message_failed";

export type AnalyticsProperties = Record<
  string,
  string | number | boolean | null | undefined
>;

declare global {
  interface Window {
    dataLayer?: Array<Record<string, unknown>>;
    gtag?: (...args: unknown[]) => void;
    posthog?: {
      capture: (event: string, properties?: AnalyticsProperties) => void;
    };
  }
}

function cleanProperties(properties: AnalyticsProperties = {}) {
  return Object.fromEntries(
    Object.entries(properties).filter(([, value]) => value !== undefined),
  );
}

export function trackEvent(
  event: AnalyticsEventName,
  properties: AnalyticsProperties = {},
) {
  if (typeof window === "undefined") return;

  const cleaned = cleanProperties(properties);
  window.dataLayer = window.dataLayer ?? [];
  window.dataLayer.push({ event, ...cleaned });

  window.gtag?.("event", event, cleaned);
  window.posthog?.capture(event, cleaned);
}
