import type { Metadata } from "next";
import { Mail, MessageSquare, Building2 } from "lucide-react";
import { PageHero, Section } from "@/components/site/page-parts";
import { ContactForm } from "@/components/site/contact-form";

export const metadata: Metadata = {
  title: "Contact — AgentMesh",
  description:
    "Talk to the AgentMesh team about early access, enterprise deployment, or partnerships.",
};

const channels = [
  {
    icon: MessageSquare,
    title: "Early access",
    description: "Get into the platform and start building on Casper Testnet.",
  },
  {
    icon: Building2,
    title: "Enterprise",
    description: "SSO, compliance, mainnet deployment, and dedicated support.",
  },
  {
    icon: Mail,
    title: "Partnerships",
    description: "Ecosystem, integrations, and co-marketing opportunities.",
  },
];

export default function ContactPage() {
  return (
    <>
      <PageHero
        eyebrow="Company"
        title="Let's talk"
        description="Tell us what you're building. Whether it's early access, an enterprise pilot, or a partnership, we'll get back to you."
      />

      <Section>
        <div className="grid grid-cols-1 gap-12 lg:grid-cols-2">
          <div className="flex flex-col gap-6">
            {channels.map((c) => {
              const Icon = c.icon;
              return (
                <div key={c.title} className="flex items-start gap-4">
                  <span className="inline-flex size-10 shrink-0 items-center justify-center rounded-lg bg-brand/10 text-brand">
                    <Icon className="size-5" />
                  </span>
                  <div>
                    <h3 className="font-heading text-base font-semibold text-foreground">
                      {c.title}
                    </h3>
                    <p className="mt-1 text-sm leading-relaxed text-muted-foreground">
                      {c.description}
                    </p>
                  </div>
                </div>
              );
            })}
            <p className="mt-2 text-sm text-muted-foreground">
              Prefer email?{" "}
              <a
                href="mailto:hello@agentmesh.world"
                className="text-brand underline-offset-4 hover:underline"
              >
                hello@agentmesh.world
              </a>
            </p>
          </div>

          <div className="rounded-2xl border border-border bg-card p-6 sm:p-8">
            <ContactForm />
          </div>
        </div>
      </Section>
    </>
  );
}
