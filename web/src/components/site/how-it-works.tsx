import Link from "next/link";
import { ArrowRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import { steps } from "@/lib/content";
import { AgentNetwork } from "@/components/site/agent-network";

export function HowItWorks() {
  return (
    <section
      id="how-it-works"
      className="relative border-t border-border bg-secondary/20 py-24 sm:py-28"
    >
      <div className="mx-auto grid max-w-7xl grid-cols-1 items-center gap-16 px-5 sm:px-8 lg:grid-cols-2">
        <div>
          <p className="flex items-center gap-3 text-xs font-medium uppercase tracking-[0.25em] text-brand">
            <span className="h-px w-6 bg-brand" />
            How It Works
          </p>

          <h2 className="mt-6 font-heading text-3xl font-bold leading-tight tracking-tight text-foreground sm:text-4xl">
            A New Way to
            <br />
            Get Things Done
          </h2>

          <ol className="mt-10 space-y-6">
            {steps.map((step) => (
              <li key={step.number} className="flex gap-4">
                <span className="mt-0.5 font-mono text-base font-bold text-brand tabular-nums">
                  {step.number}
                </span>
                <div className="flex flex-col gap-1">
                  <h3 className="font-heading text-base font-semibold text-foreground">
                    {step.title}
                  </h3>
                  <p className="max-w-sm text-sm leading-relaxed text-muted-foreground">
                    {step.description}
                  </p>
                </div>
              </li>
            ))}
          </ol>

          <Button asChild variant="link" className="mt-8 h-auto p-0 text-brand">
            <Link href="#docs">
              Learn More
              <ArrowRight className="size-4" />
            </Link>
          </Button>
        </div>

        <div className="relative">
          <AgentNetwork />
          <p className="mt-6 text-center text-xs font-semibold uppercase tracking-[0.35em] text-brand/80">
            Casper Network
          </p>
        </div>
      </div>
    </section>
  );
}
