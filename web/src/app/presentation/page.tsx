import type { Metadata } from "next";
import { headers } from "next/headers";
import { getSiteContent } from "@/lib/data/site-content";
import { PresentationExperience } from "./presentation-experience";

export const metadata: Metadata = {
  title: "Presentation — AgentMesh",
  description:
    "A full-screen AgentMesh presentation experience with video, countdown, and launch transition.",
  robots: { index: false, follow: false },
};

type PageProps = {
  searchParams: Promise<{
    video?: string;
    autoplay?: string;
  }>;
};

function youtubeIdFrom(value: string | undefined) {
  const input = (value || "").trim();
  if (!input) return "";

  try {
    const url = new URL(input);
    if (url.hostname.includes("youtu.be")) {
      return url.pathname.replace("/", "");
    }
    return url.searchParams.get("v") || url.pathname.split("/").filter(Boolean).pop() || "";
  } catch {
    return input;
  }
}

function intFrom(value: string | undefined, fallback: number) {
  const parsed = Number.parseInt(value || "", 10);
  if (!Number.isFinite(parsed)) return fallback;
  return Math.min(30, Math.max(1, parsed));
}

function safeRedirectPath(value: string | undefined) {
  const path = (value || "/").trim();
  return path.startsWith("/") && !path.startsWith("//") ? path : "/";
}

function originFromHeaders(headersList: Headers) {
  const configured =
    process.env.NEXT_PUBLIC_SITE_URL || process.env.BETTER_AUTH_URL || "";
  if (configured) {
    try {
      return new URL(configured).origin;
    } catch {
      // Fall through to request headers.
    }
  }

  const host = headersList.get("x-forwarded-host") || headersList.get("host");
  const proto = headersList.get("x-forwarded-proto") || "http";
  return host ? `${proto}://${host}` : "http://localhost:3000";
}

export default async function PresentationPage({ searchParams }: PageProps) {
  const [params, content, headersList] = await Promise.all([
    searchParams,
    getSiteContent(),
    headers(),
  ]);
  const configuredVideo =
    content["presentation.youtube"] ||
    process.env.NEXT_PUBLIC_PRESENTATION_YOUTUBE_ID ||
    "";
  const videoId = youtubeIdFrom(params.video || configuredVideo);

  return (
    <PresentationExperience
      videoId={videoId}
      startArmed={params.autoplay === "1"}
      modeLabel={content["presentation.mode_label"]}
      launchTitle={content["presentation.launch_title"]}
      launchDescription={content["presentation.launch_description"]}
      helperText={content["presentation.helper_text"]}
      countdownTitle={content["presentation.countdown_title"]}
      countdownDescription={content["presentation.countdown_description"]}
      countdownSeconds={intFrom(content["presentation.countdown_seconds"], 5)}
      redirectPath={safeRedirectPath(content["presentation.redirect_path"])}
      playerOrigin={originFromHeaders(headersList)}
    />
  );
}
