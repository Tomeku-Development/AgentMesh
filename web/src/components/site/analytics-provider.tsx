"use client";

import Script from "next/script";
import { useEffect, useRef } from "react";
import { usePathname } from "next/navigation";
import { trackEvent, type AnalyticsProperties } from "@/lib/analytics";

const GA_MEASUREMENT_ID = process.env.NEXT_PUBLIC_GA_MEASUREMENT_ID;
const POSTHOG_KEY = process.env.NEXT_PUBLIC_POSTHOG_KEY;
const POSTHOG_HOST =
  process.env.NEXT_PUBLIC_POSTHOG_HOST || "https://app.posthog.com";

function datasetProperties(el: HTMLElement): AnalyticsProperties {
  return {
    label: el.dataset.analyticsLabel,
    section: el.dataset.analyticsSection,
    placement: el.dataset.analyticsPlacement,
    destination:
      el.dataset.analyticsDestination ||
      (el instanceof HTMLAnchorElement ? el.href : undefined),
    variant: el.dataset.analyticsVariant,
  };
}

export function AnalyticsProvider() {
  const pathname = usePathname();
  const lastPageRef = useRef<string | null>(null);
  const startedFormsRef = useRef<Set<string>>(new Set());

  useEffect(() => {
    if (!POSTHOG_KEY) return;

    let mounted = true;
    void import("posthog-js").then(({ default: posthog }) => {
      if (!mounted || window.posthog) return;
      posthog.init(POSTHOG_KEY, {
        api_host: POSTHOG_HOST,
        capture_pageview: false,
        autocapture: false,
        persistence: "localStorage+cookie",
      });
      window.posthog = posthog;
    });

    return () => {
      mounted = false;
    };
  }, []);

  useEffect(() => {
    const page = `${pathname}${window.location.search}`;
    if (lastPageRef.current === page) return;
    lastPageRef.current = page;

    trackEvent("page_viewed", {
      page_path: pathname,
      page_search: window.location.search || undefined,
      page_title: document.title,
    });
  }, [pathname]);

  useEffect(() => {
    const onClick = (event: MouseEvent) => {
      const target = event.target;
      if (!(target instanceof Element)) return;

      const el = target.closest<HTMLElement>("[data-analytics-event]");
      if (!el) return;

      const eventName = el.dataset.analyticsEvent;
      if (eventName !== "cta_clicked") return;

      trackEvent("cta_clicked", datasetProperties(el));
    };

    const onFocusIn = (event: FocusEvent) => {
      const target = event.target;
      if (!(target instanceof Element)) return;

      const form = target.closest<HTMLFormElement>("[data-analytics-form]");
      if (!form) return;

      const formName = form.dataset.analyticsForm;
      if (!formName || startedFormsRef.current.has(formName)) return;

      startedFormsRef.current.add(formName);
      trackEvent("form_started", {
        form_name: formName,
        page_path: window.location.pathname,
      });
    };

    document.addEventListener("click", onClick);
    document.addEventListener("focusin", onFocusIn);
    return () => {
      document.removeEventListener("click", onClick);
      document.removeEventListener("focusin", onFocusIn);
    };
  }, []);

  return (
    <>
      {GA_MEASUREMENT_ID && (
        <>
          <Script
            src={`https://www.googletagmanager.com/gtag/js?id=${GA_MEASUREMENT_ID}`}
            strategy="afterInteractive"
          />
          <Script id="ga4-init" strategy="afterInteractive">
            {`
              window.dataLayer = window.dataLayer || [];
              function gtag(){dataLayer.push(arguments);}
              gtag('js', new Date());
              gtag('config', '${GA_MEASUREMENT_ID}', { send_page_view: false });
            `}
          </Script>
        </>
      )}
    </>
  );
}
