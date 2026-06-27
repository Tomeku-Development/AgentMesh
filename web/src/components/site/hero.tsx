import Image from "next/image";
import Link from "next/link";
import { ArrowUpRight, Play } from "lucide-react";
import { Button } from "@/components/ui/button";
import { getSiteContent } from "@/lib/data/site-content";

export async function Hero() {
  const c = await getSiteContent();
  return (
    <section className="relative isolate overflow-hidden pt-16">
      {/* Background artwork — city skyline with the AgentMesh dragon. */}
      <div className="pointer-events-none absolute inset-0 -z-10">
        <Image
          src="/images/backgrounds/hero.png"
          alt=""
          fill
          priority
          sizes="100vw"
          className="object-cover object-right"
        />
        {/* Left-to-right fade so the copy stays legible over the art. */}
        <div className="absolute inset-0 bg-gradient-to-r from-background via-background/85 to-background/30" />
        <div className="absolute inset-0 bg-gradient-to-t from-background via-transparent to-background/40" />
      </div>

      <div className="mx-auto max-w-7xl px-5 sm:px-8">
        <div className="flex min-h-[640px] max-w-2xl flex-col justify-center py-24 lg:py-32">
          <p className="animate-rise flex items-center gap-3 text-xs font-medium uppercase tracking-[0.25em] text-brand">
            <span className="h-px w-6 bg-brand" />
            {c["hero.eyebrow"]}
          </p>

          <h1 className="display-italic animate-rise delay-1 mt-6 text-5xl leading-[0.92] text-foreground sm:text-6xl lg:text-[5rem]">
            {c["hero.title_line1"]}
            <br />
            {c["hero.title_line2"]}
          </h1>

          <p className="animate-rise delay-2 mt-6 max-w-md text-base leading-relaxed text-muted-foreground sm:text-lg">
            {c["hero.description"]}
          </p>

          <div className="animate-rise delay-3 mt-9 flex flex-col gap-3 sm:flex-row sm:items-center">
            <Button
              asChild
              size="lg"
              className="h-12 rounded-md px-6 text-sm font-semibold shadow-[0_0_40px_-8px] shadow-brand/60"
            >
              <Link href="#app">
                Launch App
                <ArrowUpRight className="size-4" />
              </Link>
            </Button>
            <Button
              asChild
              size="lg"
              variant="outline"
              className="h-12 rounded-md border-border bg-background/40 px-6 text-sm font-semibold backdrop-blur"
            >
              <Link href="#how-it-works">
                <span className="flex size-5 items-center justify-center rounded-full bg-brand/15 ring-1 ring-inset ring-brand/30">
                  <Play className="size-2.5 fill-brand text-brand" />
                </span>
                See How It Works
              </Link>
            </Button>
          </div>

          <div className="animate-rise delay-4 mt-16">
            <p className="text-xs font-medium uppercase tracking-[0.2em] text-muted-foreground">
              Built On
            </p>
            <Image
              src="/images/logos/casper/Casper_Wordmark_White_RGB.png"
              alt="Casper Network"
              width={120}
              height={28}
              className="mt-3 h-6 w-auto opacity-90"
            />
          </div>
        </div>
      </div>
    </section>
  );
}
