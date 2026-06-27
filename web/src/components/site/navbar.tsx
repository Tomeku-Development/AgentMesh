"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Menu, X, ArrowUpRight, ChevronDown } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Logo } from "@/components/site/logo";
import { navMenus, type NavLink, type NavEntry } from "@/lib/content";
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
  const [openSections, setOpenSections] = useState<Set<string>>(new Set());
  const headerRef = useRef<HTMLElement>(null);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 8);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  // Close dropdowns / drawer on outside click and Escape.
  useEffect(() => {
    const onClick = (e: MouseEvent) => {
      if (headerRef.current && !headerRef.current.contains(e.target as Node)) {
        setOpenMenu(null);
      }
    };
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        setOpenMenu(null);
        setMobileOpen(false);
      }
    };
    document.addEventListener("mousedown", onClick);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", onClick);
      document.removeEventListener("keydown", onKey);
    };
  }, []);

  // Lock body scroll while the mobile drawer is open.
  useEffect(() => {
    if (!mobileOpen) return;
    const prev = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.body.style.overflow = prev;
    };
  }, [mobileOpen]);

  function toggleSection(label: string) {
    setOpenSections((cur) => {
      const next = new Set(cur);
      if (next.has(label)) next.delete(label);
      else next.add(label);
      return next;
    });
  }

  // The admin area has its own chrome.
  if (pathname?.startsWith("/admin")) return null;

  return (
    <>
      <header
        ref={headerRef}
        className={cn(
          "fixed inset-x-0 top-0 z-50 transition-colors duration-300",
          scrolled || openMenu
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
                          "size-3.5 transition-transform duration-200",
                          open && "rotate-180",
                        )}
                      />
                    </button>

                    {open && (
                      <div className="absolute left-0 top-full w-72 pt-2">
                        <div className="origin-top animate-rise overflow-hidden rounded-xl border border-border bg-card/95 p-2 shadow-2xl shadow-black/40 backdrop-blur-xl">
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

          {/* Mobile toggle — morphing hamburger ↔ X */}
          <button
            type="button"
            aria-label={mobileOpen ? "Close menu" : "Open menu"}
            aria-expanded={mobileOpen}
            onClick={() => setMobileOpen((v) => !v)}
            className="relative z-50 inline-flex size-10 cursor-pointer items-center justify-center rounded-md border border-border text-foreground transition-colors hover:bg-secondary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand/50 lg:hidden"
          >
            <span className="relative size-5">
              <Menu
                className={cn(
                  "absolute inset-0 transition-all duration-300",
                  mobileOpen
                    ? "rotate-90 scale-50 opacity-0"
                    : "rotate-0 scale-100 opacity-100",
                )}
              />
              <X
                className={cn(
                  "absolute inset-0 transition-all duration-300",
                  mobileOpen
                    ? "rotate-0 scale-100 opacity-100"
                    : "-rotate-90 scale-50 opacity-0",
                )}
              />
            </span>
          </button>
        </nav>
      </header>

      {/* Mobile drawer + backdrop (above the fixed header) */}
      <div
        className={cn(
          "fixed inset-0 z-[60] lg:hidden",
          mobileOpen ? "pointer-events-auto" : "pointer-events-none",
        )}
        aria-hidden={!mobileOpen}
      >
        {/* Backdrop */}
        <div
          onClick={() => setMobileOpen(false)}
          className={cn(
            "absolute inset-0 bg-black/60 backdrop-blur-sm transition-opacity duration-300",
            mobileOpen ? "opacity-100" : "opacity-0",
          )}
        />

        {/* Drawer */}
        <aside
          style={{ backgroundColor: "#050505" }}
          className={cn(
            "absolute right-0 top-0 flex h-full w-[86%] max-w-sm flex-col border-l border-border shadow-2xl shadow-black/50 transition-transform duration-300 ease-[cubic-bezier(0.16,1,0.3,1)]",
            mobileOpen ? "translate-x-0" : "translate-x-full",
          )}
        >
          <div className="flex h-16 items-center justify-between border-b border-border px-5">
            <Logo />
            <button
              type="button"
              aria-label="Close menu"
              onClick={() => setMobileOpen(false)}
              className="inline-flex size-9 cursor-pointer items-center justify-center rounded-md border border-border text-foreground transition-colors hover:bg-secondary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand/50"
            >
              <X className="size-5" />
            </button>
          </div>

          <div className="flex-1 overflow-y-auto overscroll-contain px-4 py-4">
            <ul className="flex flex-col gap-1">
              {navMenus.map((entry, i) => (
                <li
                  key={entry.label}
                  className={cn(mobileOpen && "animate-rise")}
                  style={
                    mobileOpen ? { animationDelay: `${60 + i * 45}ms` } : undefined
                  }
                >
                  <MobileEntry
                    entry={entry}
                    pathname={pathname}
                    open={openSections.has(entry.label)}
                    onToggle={() => toggleSection(entry.label)}
                    onNavigate={() => setMobileOpen(false)}
                  />
                </li>
              ))}
            </ul>
          </div>

          <div className="border-t border-border p-4">
            <Button asChild className="h-11 w-full rounded-md">
              <Link href="/contact" onClick={() => setMobileOpen(false)}>
                Launch App
                <ArrowUpRight className="size-4" />
              </Link>
            </Button>
          </div>
        </aside>
      </div>
    </>
  );
}

function MobileEntry({
  entry,
  pathname,
  open,
  onToggle,
  onNavigate,
}: {
  entry: NavEntry;
  pathname: string;
  open: boolean;
  onToggle: () => void;
  onNavigate: () => void;
}) {
  if (!entry.items) {
    const active = isActive(pathname, entry.href);
    return (
      <Link
        href={entry.href}
        onClick={onNavigate}
        className={cn(
          "flex items-center rounded-lg px-3 py-2.5 text-sm font-medium transition-colors",
          active
            ? "bg-brand/10 text-brand"
            : "text-foreground hover:bg-secondary",
        )}
      >
        {entry.label}
      </Link>
    );
  }

  return (
    <div>
      <button
        type="button"
        onClick={onToggle}
        aria-expanded={open}
        className="flex w-full cursor-pointer items-center justify-between rounded-lg px-3 py-2.5 text-sm font-medium text-foreground transition-colors hover:bg-secondary"
      >
        {entry.label}
        <ChevronDown
          className={cn(
            "size-4 text-muted-foreground transition-transform duration-300",
            open && "rotate-180",
          )}
        />
      </button>

      {/* Smooth height accordion via grid-rows trick */}
      <div
        className={cn(
          "grid transition-[grid-template-rows] duration-300 ease-out",
          open ? "grid-rows-[1fr]" : "grid-rows-[0fr]",
        )}
      >
        <div className="overflow-hidden">
          <div className="ml-3 mt-0.5 flex flex-col gap-0.5 border-l border-border pl-3">
            {entry.items.map((item) => (
              <MobileLink key={item.label} item={item} onNavigate={onNavigate} />
            ))}
          </div>
        </div>
      </div>
    </div>
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
    "flex items-center gap-1.5 rounded-md px-3 py-2 text-sm text-muted-foreground transition-colors hover:text-foreground";
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
