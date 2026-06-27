import { SubscribeForm } from "@/components/site/subscribe-form";
import { getSiteContent } from "@/lib/data/site-content";

export async function CTA() {
  const c = await getSiteContent();
  const titleLines = c["cta.title"].split("\n");

  return (
    <section id="app" className="relative overflow-hidden py-24 sm:py-28">
      <div className="pointer-events-none absolute left-1/2 top-1/2 -z-10 size-[600px] -translate-x-1/2 -translate-y-1/2 brand-glow opacity-60" />

      <div className="mx-auto max-w-3xl px-5 text-center sm:px-8">
        <h2 className="display-italic text-3xl leading-tight text-foreground sm:text-5xl">
          {titleLines.map((line, i) => (
            <span key={i}>
              {line}
              {i < titleLines.length - 1 && <br />}
            </span>
          ))}
        </h2>
        <p className="mx-auto mt-5 max-w-xl text-base leading-relaxed text-muted-foreground">
          {c["cta.description"]}
        </p>

        <div className="mt-9 flex justify-center">
          <SubscribeForm />
        </div>
      </div>
    </section>
  );
}
