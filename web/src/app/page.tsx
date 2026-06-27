import { Hero } from "@/components/site/hero";
import { StatsBar } from "@/components/site/stats-bar";
import { Features } from "@/components/site/features";
import { HowItWorks } from "@/components/site/how-it-works";
import { CTA } from "@/components/site/cta";
import { Reveal } from "@/components/site/reveal";

export default function Home() {
  return (
    <>
      <Hero />
      <StatsBar />
      <Reveal>
        <Features />
      </Reveal>
      <Reveal>
        <HowItWorks />
      </Reveal>
      <Reveal>
        <CTA />
      </Reveal>
    </>
  );
}
