"use client";

import Image from "next/image";
import Link from "next/link";
import { useEffect, useMemo, useRef, useState } from "react";
import {
  Maximize2,
  Play,
  RotateCcw,
  SkipForward,
  Volume2,
} from "lucide-react";

type Props = {
  videoId: string;
  startArmed?: boolean;
  modeLabel: string;
  launchTitle: string;
  launchDescription: string;
  helperText: string;
  countdownTitle: string;
  countdownDescription: string;
  countdownSeconds: number;
  redirectPath: string;
  playerOrigin: string;
};

function youtubeSrc(videoId: string, started: boolean, playerOrigin: string) {
  const params = new URLSearchParams({
    enablejsapi: "1",
    rel: "0",
    controls: "1",
    modestbranding: "1",
    playsinline: "0",
    origin: playerOrigin,
  });
  if (started) params.set("autoplay", "1");
  return `https://www.youtube.com/embed/${videoId}?${params.toString()}`;
}

function postToPlayer(iframe: HTMLIFrameElement | null, func: string, args: unknown[] = []) {
  iframe?.contentWindow?.postMessage(
    JSON.stringify({ event: "command", func, args }),
    "https://www.youtube.com",
  );
}

export function PresentationExperience({
  videoId,
  startArmed = false,
  modeLabel,
  launchTitle,
  launchDescription,
  helperText,
  countdownTitle,
  countdownDescription,
  countdownSeconds,
  redirectPath,
  playerOrigin,
}: Props) {
  const iframeRef = useRef<HTMLIFrameElement>(null);
  const stageRef = useRef<HTMLDivElement>(null);
  const [started, setStarted] = useState(startArmed);
  const [ended, setEnded] = useState(false);
  const [countdown, setCountdown] = useState(countdownSeconds);
  const [fullscreenFailed, setFullscreenFailed] = useState(false);

  const src = useMemo(
    () => (videoId ? youtubeSrc(videoId, started, playerOrigin) : ""),
    [playerOrigin, videoId, started],
  );

  useEffect(() => {
    if (!started) return;
    const timer = window.setTimeout(() => {
      postToPlayer(iframeRef.current, "playVideo");
      postToPlayer(iframeRef.current, "unMute");
    }, 650);
    return () => window.clearTimeout(timer);
  }, [started, src]);

  useEffect(() => {
    function onMessage(event: MessageEvent) {
      if (!String(event.origin).includes("youtube.com")) return;
      let data: { event?: string; info?: number } | null = null;
      try {
        data =
          typeof event.data === "string"
            ? JSON.parse(event.data || "{}")
            : event.data;
      } catch {
        return;
      }
      if (data?.event === "onStateChange" && data?.info === 0) {
        setEnded(true);
        setCountdown(countdownSeconds);
      }
    }

    window.addEventListener("message", onMessage);
    return () => window.removeEventListener("message", onMessage);
  }, [countdownSeconds]);

  useEffect(() => {
    if (!ended) return;
    if (countdown <= 0) {
      window.location.href = redirectPath;
      return;
    }
    const timer = window.setTimeout(() => setCountdown((value) => value - 1), 1000);
    return () => window.clearTimeout(timer);
  }, [countdown, ended, redirectPath]);

  async function launchPresentation() {
    setStarted(true);
    setFullscreenFailed(false);
    try {
      await stageRef.current?.requestFullscreen();
    } catch {
      setFullscreenFailed(true);
    }
  }

  async function replay() {
    setEnded(false);
    setCountdown(countdownSeconds);
    setStarted(true);
    try {
      await stageRef.current?.requestFullscreen();
    } catch {
      setFullscreenFailed(true);
    }
    window.setTimeout(() => {
      postToPlayer(iframeRef.current, "seekTo", [0, true]);
      postToPlayer(iframeRef.current, "playVideo");
    }, 250);
  }

  function skipToSite() {
    window.location.href = redirectPath;
  }

  return (
    <main
      ref={stageRef}
      className="relative min-h-screen overflow-hidden bg-black text-white"
    >
      <div className="absolute inset-0">
        <Image
          src="/images/backgrounds/hero.png"
          alt=""
          fill
          priority
          className="object-cover opacity-30"
        />
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_20%,rgba(255,106,0,0.35),transparent_36%),linear-gradient(180deg,rgba(0,0,0,0.35),#050505_78%)]" />
        <div className="presentation-speed-lines absolute inset-0 opacity-40" />
      </div>

      <div className="relative z-10 flex min-h-screen flex-col">
        <header className="flex min-h-16 items-center justify-between gap-4 px-5 py-4 sm:px-8">
          <Link href="/" className="inline-flex items-center">
            <Image
              src="/images/logos/agentmesh/AgentMesh_Wordmark_White_RGB.png"
              alt="AgentMesh"
              width={148}
              height={32}
              className="h-6 w-auto sm:h-7"
              priority
            />
          </Link>
          <div className="flex min-w-0 items-center gap-2 text-right text-[10px] uppercase tracking-[0.18em] text-white/55 sm:text-xs sm:tracking-[0.24em]">
            <span className="size-1.5 rounded-full bg-brand" />
            <span className="truncate">{modeLabel}</span>
          </div>
        </header>

        <section className="flex flex-1 items-center justify-center px-4 pb-8 pt-2">
          <div className="w-full max-w-6xl">
            <div className="relative aspect-video min-h-[320px] overflow-hidden rounded-lg border border-white/10 bg-black shadow-[0_40px_120px_rgba(0,0,0,0.7)] sm:min-h-0">
              {videoId ? (
                <iframe
                  ref={iframeRef}
                  key={src}
                  src={src}
                  title="AgentMesh presentation video"
                  allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
                  allowFullScreen
                  className="absolute inset-0 size-full"
                />
              ) : (
                <div className="flex size-full flex-col items-center justify-center bg-black px-6 text-center">
                  <p className="font-heading text-2xl font-bold sm:text-3xl">
                    Add a YouTube video
                  </p>
                  <p className="mt-3 max-w-lg text-sm leading-relaxed text-white/60">
                    Add it in <span className="text-white">Admin → Website settings → Presentation</span>,
                    or open this page with <code>?video=YOUTUBE_ID</code>.
                  </p>
                </div>
              )}

              {!started && !ended && (
                <button
                  type="button"
                  onClick={launchPresentation}
                  disabled={!videoId}
                  className="absolute inset-0 flex cursor-pointer flex-col items-center justify-center bg-black/60 p-6 text-center backdrop-blur-sm transition-colors hover:bg-black/50 disabled:cursor-not-allowed"
                >
                  <span className="inline-flex size-20 items-center justify-center rounded-full bg-brand text-black shadow-[0_0_70px_rgba(255,106,0,0.65)]">
                    <Play className="ml-1 size-9 fill-current" />
                  </span>
                  <span className="mt-7 font-heading text-4xl font-black uppercase italic tracking-normal sm:text-6xl">
                    {launchTitle}
                  </span>
                  <span className="mt-3 max-w-xl text-sm leading-relaxed text-white/65">
                    {launchDescription}
                  </span>
                </button>
              )}

              {ended && (
                <div className="absolute inset-0 flex flex-col items-center justify-center overflow-hidden bg-black/85 p-6 text-center backdrop-blur-md">
                  <div className="presentation-countdown-ring">
                    <span className="font-heading text-7xl font-black italic text-brand sm:text-9xl">
                      {countdown}
                    </span>
                  </div>
                  <p className="mt-8 font-heading text-3xl font-black uppercase italic sm:text-5xl">
                    {countdownTitle}
                  </p>
                  <p className="mt-3 max-w-lg text-sm text-white/60">
                    {countdownDescription}
                  </p>
                  <div className="mt-8 flex flex-wrap items-center justify-center gap-3">
                    <button
                      type="button"
                      onClick={replay}
                      className="inline-flex h-10 items-center gap-2 rounded-md border border-white/15 bg-white/10 px-4 text-sm font-semibold text-white transition-colors hover:bg-white/15"
                    >
                      <RotateCcw className="size-4" />
                      Play again
                    </button>
                    <button
                      type="button"
                      onClick={skipToSite}
                      className="inline-flex h-10 items-center gap-2 rounded-md bg-brand px-4 text-sm font-semibold text-black transition-all hover:brightness-110"
                    >
                      <SkipForward className="size-4" />
                      Go now
                    </button>
                  </div>
                </div>
              )}
            </div>

            <div className="mt-5 flex flex-wrap items-center justify-between gap-3 text-xs text-white/55">
              <div className="flex items-center gap-2">
                <Volume2 className="size-4 text-brand" />
                {helperText}
              </div>
              <button
                type="button"
                onClick={launchPresentation}
                className="inline-flex items-center gap-2 rounded-md border border-white/10 px-3 py-2 text-white/70 transition-colors hover:bg-white/10 hover:text-white"
              >
                <Maximize2 className="size-3.5" />
                Fullscreen
              </button>
            </div>

            {fullscreenFailed && (
              <p className="mt-3 rounded-md border border-warning/30 bg-warning/10 px-3 py-2 text-xs text-warning">
                Fullscreen was blocked by the browser. Press the fullscreen button or
                use the browser shortcut.
              </p>
            )}
          </div>
        </section>
      </div>
    </main>
  );
}
