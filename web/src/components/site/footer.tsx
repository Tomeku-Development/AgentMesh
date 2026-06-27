import Image from "next/image";
import Link from "next/link";
import { ArrowUpRight } from "lucide-react";
import { Logo } from "@/components/site/logo";
import { footer } from "@/lib/content";

export function Footer() {
  return (
    <footer className="border-t border-border bg-background">
      <div className="mx-auto max-w-7xl px-5 py-16 sm:px-8">
        <div className="grid grid-cols-2 gap-10 lg:grid-cols-5">
          <div className="col-span-2">
            <Logo />
            <p className="mt-4 max-w-xs text-sm leading-relaxed text-muted-foreground">
              The decentralized operating system for autonomous organizations,
              powered by a multi-agent network on Casper.
            </p>
            <div className="mt-6 flex items-center gap-2">
              <span className="text-xs uppercase tracking-[0.2em] text-muted-foreground">
                Built on
              </span>
              <Image
                src="/images/logos/casper/Casper_Wordmark_White_RGB.png"
                alt="Casper Network"
                width={96}
                height={22}
                className="h-5 w-auto opacity-80"
              />
            </div>
          </div>

          {footer.columns.map((column) => (
            <div key={column.title}>
              <h3 className="text-sm font-semibold text-foreground">
                {column.title}
              </h3>
              <ul className="mt-4 space-y-3">
                {column.links.map((link) => (
                  <li key={link.label}>
                    {"external" in link && link.external ? (
                      <a
                        href={link.href}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-1 text-sm text-muted-foreground transition-colors hover:text-foreground"
                      >
                        {link.label}
                        <ArrowUpRight className="size-3" />
                      </a>
                    ) : (
                      <Link
                        href={link.href}
                        className="text-sm text-muted-foreground transition-colors hover:text-foreground"
                      >
                        {link.label}
                      </Link>
                    )}
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        <div className="mt-14 flex flex-col items-center justify-between gap-4 border-t border-border pt-8 sm:flex-row">
          <p className="text-xs text-muted-foreground">
            © {new Date().getFullYear()} AgentMesh. All rights reserved.
          </p>
          <div className="flex items-center gap-6">
            {footer.legal.map((link) => (
              <Link
                key={link.label}
                href={link.href}
                className="text-xs text-muted-foreground transition-colors hover:text-foreground"
              >
                {link.label}
              </Link>
            ))}
          </div>
        </div>
      </div>
    </footer>
  );
}
