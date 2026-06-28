import type { Metadata } from "next";
import Link from "next/link";
import { Check } from "lucide-react";
import { PageHero, Section, SectionTitle } from "@/components/site/page-parts";
import { Button } from "@/components/ui/button";
import { pricingTiers, pricingFaqs } from "@/lib/content";
import { cn } from "@/lib/utils";

export const metadata: Metadata = {
  title: "Pricing — AgentMesh",
  description:
    "Plans for builders, teams, and enterprises. Start free on Casper Testnet and scale to mainnet with compliance controls.",
};

export default function PricingPage() {
  return (
    <>
      <PageHero
        eyebrow="Pricing"
        title="Start free. Scale with trust."
        description="Build on Casper Testnet for free, then upgrade as your organizations and workflows grow. AI usage is billed transparently."
      />

      <Section>
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
          {pricingTiers.map((tier) => (
            <div
              key={tier.name}
              className={cn(
                "relative flex flex-col rounded-2xl border p-7",
                tier.highlighted
                  ? "border-brand/50 bg-card shadow-[0_0_60px_-20px] shadow-brand/50"
                  : "border-border bg-card",
              )}
            >
              {tier.highlighted && (
                <span className="absolute -top-3 left-7 rounded-full bg-brand px-3 py-1 text-[11px] font-semibold uppercase tracking-wider text-primary-foreground">
                  Most popular
                </span>
              )}
              <h3 className="font-heading text-lg font-semibold text-foreground">
                {tier.name}
              </h3>
              <div className="mt-4 flex items-baseline gap-1">
                <span className="font-heading text-4xl font-bold text-foreground">
                  {tier.price}
                </span>
                {tier.cadence && (
                  <span className="text-sm text-muted-foreground">
                    {tier.cadence}
                  </span>
                )}
              </div>
              <p className="mt-3 text-sm leading-relaxed text-muted-foreground">
                {tier.description}
              </p>

              <ul className="mt-6 flex-1 space-y-3">
                {tier.features.map((f) => (
                  <li key={f} className="flex items-start gap-2.5 text-sm">
                    <Check className="mt-0.5 size-4 shrink-0 text-brand" />
                    <span className="text-muted-foreground">{f}</span>
                  </li>
                ))}
              </ul>

              {tier.name === "Pro" ? (
                <form action="/api/checkout" method="POST" className="mt-8">
                  <input type="hidden" name="plan" value="pro" />
                  <input type="hidden" name="provider" value="xendit" />
                  <Button
                    type="submit"
                    className="h-11 w-full rounded-md"
                    data-analytics-event="cta_clicked"
                    data-analytics-label="checkout_pro"
                    data-analytics-section="pricing"
                    data-analytics-placement="pro"
                    data-analytics-destination="/api/checkout"
                  >
                    Checkout with Xendit
                  </Button>
                </form>
              ) : (
                <Button
                  asChild
                  className={cn(
                    "mt-8 h-11 w-full rounded-md",
                    !tier.highlighted &&
                      "bg-secondary text-secondary-foreground hover:bg-secondary/80",
                  )}
                  variant={tier.highlighted ? "default" : "secondary"}
                >
                  <Link
                    href={tier.cta.href}
                    data-analytics-event="cta_clicked"
                    data-analytics-label={tier.cta.label.toLowerCase().replace(/\s+/g, "_")}
                    data-analytics-section="pricing"
                    data-analytics-placement={tier.name.toLowerCase().replace(/\s+/g, "_")}
                    data-analytics-destination={tier.cta.href}
                  >
                    {tier.cta.label}
                  </Link>
                </Button>
              )}
            </div>
          ))}
        </div>
      </Section>

      <Section className="border-t border-border bg-secondary/20">
        <SectionTitle eyebrow="FAQ" title="Common questions" />
        <div className="mt-10 grid grid-cols-1 gap-6 md:grid-cols-2">
          {pricingFaqs.map((faq) => (
            <div
              key={faq.question}
              className="rounded-xl border border-border bg-card p-6"
            >
              <h3 className="font-heading text-base font-semibold text-foreground">
                {faq.question}
              </h3>
              <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
                {faq.answer}
              </p>
            </div>
          ))}
        </div>
      </Section>
    </>
  );
}
