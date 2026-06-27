"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Menu, X, ArrowUpRight, ChevronDown } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Logo } from "@/components/site/logo";
import { navMenus, type NavLink } from "@/lib/content";
import { cn } from "@/lib/utils";

function isActive(pathname: string, href: string) {
  if (href === "/") return pathname === "/";
  return pathname === href || pathname.startsWith(`${href}/`);
}

export function Navbar() {
  const pathname = usePathname();
  const [scrolled, setScrolled] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const [openMenu, setOpenMenu] = useState<string | null>(null);
  const headerRef = useRef<HTMLElement>(null);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 8);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  // Close dropdowns on outside click / Escape.
  useEffect(() => {
    const onClick = (e: MouseEvent) => {
      if (headerRef.current && !headerRef.current.contains(e.target as Node)) {
        setOpenMenu(null);
      }
    };
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") setOpenMenu(null);
    };
    document.addEventListener("mousedown", onClick);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", onClick);
      document.removeEventListener("keydown", onKey);
    };
  }, []);

  // The admin area has its own chrome.
  if (pathname?.startsWith("/admin")) return null;

  return (
    <header
      ref={headerRef}
      className={cn(
        "fixed inset-x-0 top-0 z-50 transition-colors duration-300",
        scrolled || openMenu || mobileOpen
          ? "border-b border-border bg-background/85 backdrop-blur-xl"
          : "border-b border-transparent",
      )}
    >
      <nav className="mx-auto flex h-16 max-w-7xl items-center justify-between gap-6 px-5 sm:px-8">
        <Logo />

        {/* Desktop nav */}
        <ul className="hidden items-center gap-1 lg:flex">
          {navMenus.map((entry) => {
            if (entry.items) {
              const open = openMenu === entry.label;
              const groupActive = entry.items.some(
                (i) => !i.external && isActive(pathname, i.href),
              );
              return (
                <li
                  key={entry.label}
                  className="relative"
                  onMouseEnter={() => setOpenMenu(entry.label)}
                  onMouseLeave={() => setOpenMenu(null)}
                >
                  <button
                    type="button"
                    aria-expanded={open}
                    aria-haspopup="true"
                    onClick={() =>
                      setOpenMenu((cur) =>
                        cur === entry.label ? null : entry.label,
                      )
                    }
                    className={cn(
                      "inline-flex cursor-pointer items-center gap-1 rounded-md px-3 py-2 text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand/50",
                      groupActive || open
                        ? "text-foreground"
                        : "text-muted-foreground hover:text-foreground",
                    )}
                  >
                    {entry.label}
                    <ChevronDown
                      className={cn(
                        "size-3.5 transition-transform",
                        open && "rotate-180",
                      )}
                    />
                  </button>

                  {open && (
                    <div className="absolute left-0 top-full w-72 pt-2">
                      <div className="overflow-hidden rounded-xl border border-border bg-card/95 p-2 shadow-2xl shadow-black/40 backdrop-blur-xl">
                        {entry.items.map((item) => (
                          <DropdownItem
                            key={item.label}
                            item={item}
                            active={
                              !item.external && isActive(pathname, item.href)
                            }
                            onSelect={() => setOpenMenu(null)}
                          />
                        ))}
                      </div>
                    </div>
                  )}
                </li>
              );
            }

            const active = isActive(pathname, entry.href);
            return (
              <li key={entry.label}>
                <Link
                  href={entry.href}
                  className={cn(
                    "rounded-md px-3 py-2 text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand/50",
                    active
                      ? "text-foreground"
                      : "text-muted-foreground hover:text-foreground",
                  )}
                >
                  {entry.label}
                </Link>
              </li>
            );
          })}
        </ul>

        <div className="hidden items-center gap-3 lg:flex">
          <Button
            asChild
            variant="outline"
            className="rounded-md border-border bg-transparent"
          >
            <Link href="/contact">
              Launch App
              <ArrowUpRight className="size-4" />
            </Link>
          </Button>
        </div>

        <button
          type="button"
          aria-label="Toggle menu"
          aria-expanded={mobileOpen}
          onClick={() => setMobileOpen((v) => !v)}
          className="inline-flex size-10 cursor-pointer items-center justify-center rounded-md border border-border text-foreground transition-colors hover:bg-secondary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand/50 lg:hidden"
        >
          {mobileOpen ? <X className="size-5" /> : <Menu className="size-5" />}
        </button>
      </nav>

      {/* Mobile nav */}
      {mobileOpen && (
        <div className="max-h-[calc(100vh-4rem)] overflow-y-auto border-t border-border bg-background/95 backdrop-blur-xl lg:hidden">
          <div className="mx-auto flex max-w-7xl flex-col gap-1 px-5 py-4 sm:px-8">
            {navMenus.map((entry) =>
              entry.items ? (
                <div key={entry.label} className="py-1">
                  <p className="px-3 py-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                    {entry.label}
                  </p>
                  {entry.items.map((item) => (
                    <MobileLink
                      key={item.label}
                      item={item}
                      onNavigate={() => setMobileOpen(false)}
                    />
                  ))}
                </div>
              ) : (
                <Link
                  key={entry.label}
                  href={entry.href}
                  onClick={() => setMobileOpen(false)}
                  className="block rounded-md px-3 py-2.5 text-sm font-medium text-muted-foreground transition-colors hover:bg-secondary hover:text-foreground"
                >
                  {entry.label}
                </Link>
              ),
            )}
            <Button asChild className="mt-3 w-full rounded-md">
              <Link href="/contact" onClick={() => setMobileOpen(false)}>
                Launch App
                <ArrowUpRight className="size-4" />
              </Link>
            </Button>
          </div>
        </div>
      )}
    </header>
  );
}

function DropdownItem({
  item,
  active,
  onSelect,
}: {
  item: NavLink;
  active: boolean;
  onSelect: () => void;
}) {
  const className = cn(
    "block rounded-lg px-3 py-2.5 transition-colors",
    active ? "bg-secondary" : "hover:bg-secondary/70",
  );
  const inner = (
    <>
      <span className="flex items-center gap-1.5 text-sm font-medium text-foreground">
        {item.label}
        {item.external && (
          <ArrowUpRight className="size-3 text-muted-foreground" />
        )}
      </span>
      {item.description && (
        <span className="mt-0.5 block text-xs leading-snug text-muted-foreground">
          {item.description}
        </span>
      )}
    </>
  );

  if (item.external) {
    return (
      <a
        href={item.href}
        target="_blank"
        rel="noopener noreferrer"
        className={className}
        onClick={onSelect}
      >
        {inner}
      </a>
    );
  }
  return (
    <Link href={item.href} className={className} onClick={onSelect}>
      {inner}
    </Link>
  );
}

function MobileLink({
  item,
  onNavigate,
}: {
  item: NavLink;
  onNavigate: () => void;
}) {
  const className =
    "flex items-center gap-1.5 rounded-md px-3 py-2.5 text-sm font-medium text-muted-foreground transition-colors hover:bg-secondary hover:text-foreground";
  if (item.external) {
    return (
      <a
        href={item.href}
        target="_blank"
        rel="noopener noreferrer"
        onClick={onNavigate}
        className={className}
      >
        {item.label}
        <ArrowUpRight className="size-3" />
      </a>
    );
  }
  return (
    <Link href={item.href} onClick={onNavigate} className={className}>
      {item.label}
    </Link>
  );
}
