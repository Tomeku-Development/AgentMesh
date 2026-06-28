"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import Image from "next/image";
import { usePathname, useRouter } from "next/navigation";
import {
  LayoutDashboard,
  FileText,
  Image as ImageIcon,
  BookText,
  Mail,
  MessageSquare,
  Activity,
  BarChart3,
  BookOpen,
  Bug,
  Building2,
  CreditCard,
  Settings,
  Users,
  Search,
  Bell,
  HelpCircle,
  PanelLeftClose,
  PanelLeftOpen,
  ArrowUpRight,
  LogOut,
  ChevronsUpDown,
  UserCircle,
  type LucideIcon,
} from "lucide-react";
import { authClient } from "@/lib/auth-client";
import { cn } from "@/lib/utils";

type Item = { href: string; label: string; icon: LucideIcon; soon?: boolean };
type Group = { title: string; items: Item[] };

const GROUPS: Group[] = [
  {
    title: "Workspace",
    items: [{ href: "/admin", label: "Overview", icon: LayoutDashboard }],
  },
  {
    title: "Content",
    items: [
      { href: "/admin/content", label: "Pages & Content", icon: FileText },
      { href: "/admin/docs", label: "Documentation", icon: BookText },
      { href: "/admin/media", label: "Media", icon: ImageIcon },
    ],
  },
  {
    title: "Audience",
    items: [
      { href: "/admin/subscribers", label: "Subscribers", icon: Mail },
      { href: "/admin/messages", label: "Messages", icon: MessageSquare },
    ],
  },
  {
    title: "Insights",
    items: [
      { href: "/admin/stats", label: "Network Stats", icon: Activity },
      { href: "/admin/analytics", label: "Analytics", icon: BarChart3 },
      { href: "/admin/sales", label: "Sales", icon: CreditCard },
      { href: "/admin/reports", label: "Reports", icon: Bug },
    ],
  },
  {
    title: "System",
    items: [
      { href: "/admin/users", label: "Users & Roles", icon: Users },
      { href: "/admin/organization", label: "Organization", icon: Building2 },
      { href: "/admin/settings", label: "Website settings", icon: Settings },
    ],
  },
];

type User = { name: string; email: string; role: string };
type Notification = {
  title: string;
  detail: string;
  href: string;
  tone: "info" | "warning" | "success";
};

export function AdminShell({
  workspace,
  user,
  notifications = [],
  initialCollapsed = false,
  children,
}: {
  workspace: string;
  user: User;
  notifications?: Notification[];
  initialCollapsed?: boolean;
  children: React.ReactNode;
}) {
  const router = useRouter();
  const pathname = usePathname();
  const [collapsed, setCollapsed] = useState(initialCollapsed);
  const [mobileOpen, setMobileOpen] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);
  const [notificationsOpen, setNotificationsOpen] = useState(false);
  const [helpOpen, setHelpOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);
  const notificationsRef = useRef<HTMLDivElement>(null);
  const helpRef = useRef<HTMLDivElement>(null);

  const isActive = (href: string) =>
    href === "/admin" ? pathname === "/admin" : pathname.startsWith(href);

  useEffect(() => {
    const onClick = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setMenuOpen(false);
      }
      if (
        notificationsRef.current &&
        !notificationsRef.current.contains(e.target as Node)
      ) {
        setNotificationsOpen(false);
      }
      if (helpRef.current && !helpRef.current.contains(e.target as Node)) {
        setHelpOpen(false);
      }
    };
    document.addEventListener("mousedown", onClick);
    return () => document.removeEventListener("mousedown", onClick);
  }, []);

  function toggleCollapse() {
    setCollapsed((c) => {
      const next = !c;
      document.cookie = `am_admin_collapsed=${next ? "1" : "0"};path=/;max-age=31536000`;
      return next;
    });
  }

  async function signOut() {
    await authClient.signOut();
    router.push("/admin/login");
    router.refresh();
  }

  const initials =
    user.name
      .split(" ")
      .map((p) => p[0])
      .filter(Boolean)
      .slice(0, 2)
      .join("")
      .toUpperCase() || "AM";

  return (
    <div className="min-h-screen bg-background">
      {/* Sidebar */}
      <aside
        className={cn(
          "fixed inset-y-0 left-0 z-40 flex flex-col border-r border-border bg-sidebar transition-[width,transform] duration-200",
          collapsed ? "w-[72px]" : "w-[260px]",
          mobileOpen ? "translate-x-0" : "-translate-x-full lg:translate-x-0",
        )}
      >
        <div className="flex h-16 items-center px-4">
          <Image
            src={
              collapsed
                ? "/images/logos/agentmesh/AgentMesh_App_Icon_Orange.png"
                : "/images/logos/agentmesh/AgentMesh_Wordmark_White_RGB.png"
            }
            alt="AgentMesh"
            width={collapsed ? 28 : 130}
            height={28}
            className={collapsed ? "size-7" : "h-6 w-auto"}
          />
        </div>

        <nav className="flex-1 overflow-y-auto px-3 py-2">
          {GROUPS.map((group) => (
            <div key={group.title} className="mb-4">
              {!collapsed && (
                <p className="px-3 pb-1.5 pt-2 text-[10px] font-semibold uppercase tracking-[0.12em] text-muted-foreground/70">
                  {group.title}
                </p>
              )}
              <ul className="flex flex-col gap-0.5">
                {group.items.map((item) => {
                  const Icon = item.icon;
                  const active = !item.soon && isActive(item.href);
                  const inner = (
                    <>
                      <Icon className="size-[18px] shrink-0" />
                      {!collapsed && (
                        <span className="flex-1 truncate">{item.label}</span>
                      )}
                      {!collapsed && item.soon && (
                        <span className="rounded bg-secondary px-1.5 py-0.5 text-[9px] font-semibold uppercase tracking-wide text-muted-foreground">
                          Soon
                        </span>
                      )}
                    </>
                  );
                  const base =
                    "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors";
                  return (
                    <li key={item.href}>
                      {item.soon ? (
                        <span
                          title={collapsed ? `${item.label} (soon)` : undefined}
                          className={cn(
                            base,
                            "cursor-not-allowed text-muted-foreground/50",
                          )}
                        >
                          {inner}
                        </span>
                      ) : (
                        <Link
                          href={item.href}
                          title={collapsed ? item.label : undefined}
                          onClick={() => setMobileOpen(false)}
                          className={cn(
                            base,
                            active
                              ? "bg-brand/10 text-brand"
                              : "text-muted-foreground hover:bg-secondary hover:text-foreground",
                          )}
                        >
                          {inner}
                        </Link>
                      )}
                    </li>
                  );
                })}
              </ul>
            </div>
          ))}
        </nav>

        <div className="border-t border-border p-3">
          <div className="flex flex-col gap-0.5">
            <Link
              href="/"
              className={cn(
                "flex items-center gap-3 rounded-lg px-3 py-2 text-sm text-muted-foreground transition-colors hover:bg-secondary hover:text-foreground",
                collapsed && "justify-center",
              )}
              title="View site"
            >
              <ArrowUpRight className="size-[18px]" />
              {!collapsed && "View site"}
            </Link>
            <button
              type="button"
              onClick={toggleCollapse}
              className={cn(
                "hidden cursor-pointer items-center gap-3 rounded-lg px-3 py-2 text-sm text-muted-foreground transition-colors hover:bg-secondary hover:text-foreground lg:flex",
                collapsed && "justify-center",
              )}
            >
              {collapsed ? (
                <PanelLeftOpen className="size-[18px]" />
              ) : (
                <>
                  <PanelLeftClose className="size-[18px]" />
                  Collapse
                </>
              )}
            </button>
          </div>
        </div>
      </aside>

      {/* Mobile overlay */}
      {mobileOpen && (
        <div
          className="fixed inset-0 z-30 bg-black/60 lg:hidden"
          onClick={() => setMobileOpen(false)}
          aria-hidden
        />
      )}

      {/* Main column */}
      <div
        className={cn(
          "flex min-h-screen flex-col transition-[padding] duration-200",
          collapsed ? "lg:pl-[72px]" : "lg:pl-[260px]",
        )}
      >
        {/* Topbar */}
        <header className="sticky top-0 z-20 flex h-16 items-center gap-3 border-b border-border bg-background/85 px-4 backdrop-blur-xl sm:px-6">
          <button
            type="button"
            onClick={() => setMobileOpen(true)}
            className="inline-flex size-9 cursor-pointer items-center justify-center rounded-md border border-border text-foreground lg:hidden"
            aria-label="Open menu"
          >
            <PanelLeftOpen className="size-5" />
          </button>

          <div className="relative hidden max-w-md flex-1 sm:block">
            <Search className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
            <input
              type="search"
              placeholder="Search anything..."
              className="h-9 w-full rounded-lg border border-border bg-card pl-9 pr-12 text-sm text-foreground outline-none transition-colors placeholder:text-muted-foreground focus:border-brand/50 focus:ring-2 focus:ring-brand/20"
            />
            <kbd className="pointer-events-none absolute right-2.5 top-1/2 -translate-y-1/2 rounded border border-border bg-secondary px-1.5 py-0.5 font-mono text-[10px] text-muted-foreground">
              ⌘K
            </kbd>
          </div>

          <div className="ml-auto flex items-center gap-1.5">
            <div className="relative" ref={notificationsRef}>
              <button
                type="button"
                onClick={() => setNotificationsOpen((open) => !open)}
                className="relative inline-flex size-9 cursor-pointer items-center justify-center rounded-md text-muted-foreground transition-colors hover:bg-secondary hover:text-foreground"
                aria-label="Notifications"
                aria-expanded={notificationsOpen}
              >
                <Bell className="size-[18px]" />
                {notifications.length > 0 && (
                  <span className="absolute right-2 top-2 size-1.5 rounded-full bg-brand" />
                )}
              </button>
              {notificationsOpen && (
                <div className="absolute right-0 top-full mt-2 w-80 overflow-hidden rounded-xl border border-border bg-card shadow-2xl shadow-black/40">
                  <div className="flex items-center justify-between border-b border-border px-4 py-3">
                    <p className="text-sm font-semibold text-foreground">
                      Notifications
                    </p>
                    <span className="text-xs text-muted-foreground">
                      {notifications.length}
                    </span>
                  </div>
                  {notifications.length === 0 ? (
                    <p className="px-4 py-8 text-center text-sm text-muted-foreground">
                      Nothing needs attention.
                    </p>
                  ) : (
                    <div className="divide-y divide-border">
                      {notifications.map((item) => (
                        <Link
                          key={`${item.title}-${item.href}`}
                          href={item.href}
                          onClick={() => setNotificationsOpen(false)}
                          className="block px-4 py-3 transition-colors hover:bg-secondary"
                        >
                          <div className="flex gap-3">
                            <span
                              className={cn(
                                "mt-1 size-2 shrink-0 rounded-full",
                                item.tone === "warning"
                                  ? "bg-warning"
                                  : item.tone === "success"
                                    ? "bg-success"
                                    : "bg-brand",
                              )}
                            />
                            <div className="min-w-0">
                              <p className="truncate text-sm font-medium text-foreground">
                                {item.title}
                              </p>
                              <p className="mt-0.5 line-clamp-2 text-xs text-muted-foreground">
                                {item.detail}
                              </p>
                            </div>
                          </div>
                        </Link>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>
            <div className="relative" ref={helpRef}>
              <button
                type="button"
                onClick={() => setHelpOpen((open) => !open)}
                className="inline-flex size-9 cursor-pointer items-center justify-center rounded-md text-muted-foreground transition-colors hover:bg-secondary hover:text-foreground"
                aria-label="Help"
                aria-expanded={helpOpen}
              >
                <HelpCircle className="size-[18px]" />
              </button>
              {helpOpen && (
                <div className="absolute right-0 top-full mt-2 w-72 overflow-hidden rounded-xl border border-border bg-card p-1.5 shadow-2xl shadow-black/40">
                  <Link
                    href="/admin/reports"
                    onClick={() => setHelpOpen(false)}
                    className="flex items-center gap-2.5 rounded-lg px-3 py-2 text-sm text-muted-foreground transition-colors hover:bg-secondary hover:text-foreground"
                  >
                    <BarChart3 className="size-4" />
                    Reports & readiness
                  </Link>
                  <Link
                    href="/admin/sales"
                    onClick={() => setHelpOpen(false)}
                    className="flex items-center gap-2.5 rounded-lg px-3 py-2 text-sm text-muted-foreground transition-colors hover:bg-secondary hover:text-foreground"
                  >
                    <CreditCard className="size-4" />
                    Sales & payments
                  </Link>
                  <Link
                    href="/admin/docs"
                    onClick={() => setHelpOpen(false)}
                    className="flex items-center gap-2.5 rounded-lg px-3 py-2 text-sm text-muted-foreground transition-colors hover:bg-secondary hover:text-foreground"
                  >
                    <BookOpen className="size-4" />
                    Documentation CMS
                  </Link>
                  <a
                    href="mailto:admin@agentmesh.world?subject=AgentMesh%20admin%20bug%20report"
                    className="flex items-center gap-2.5 rounded-lg px-3 py-2 text-sm text-muted-foreground transition-colors hover:bg-secondary hover:text-foreground"
                  >
                    <Bug className="size-4" />
                    Report bug
                  </a>
                </div>
              )}
            </div>
            <div className="mx-1 h-6 w-px bg-border" />

            {/* User menu */}
            <div className="relative" ref={menuRef}>
              <button
                type="button"
                onClick={() => setMenuOpen((v) => !v)}
                aria-expanded={menuOpen}
                className="flex cursor-pointer items-center gap-2.5 rounded-lg px-2 py-1.5 transition-colors hover:bg-secondary"
              >
                <span className="flex size-8 items-center justify-center rounded-full bg-brand/15 text-xs font-bold text-brand">
                  {initials}
                </span>
                <span className="hidden leading-tight text-left sm:block">
                  <span className="block text-sm font-medium text-foreground">
                    {user.name}
                  </span>
                  <span className="block text-[11px] capitalize text-muted-foreground">
                    {user.role} · {workspace}
                  </span>
                </span>
                <ChevronsUpDown className="hidden size-3.5 text-muted-foreground sm:block" />
              </button>

              {menuOpen && (
                <div className="absolute right-0 top-full mt-2 w-60 overflow-hidden rounded-xl border border-border bg-card p-1.5 shadow-2xl shadow-black/40">
                  <div className="border-b border-border px-3 py-2.5">
                    <p className="truncate text-sm font-medium text-foreground">
                      {user.name}
                    </p>
                    <p className="truncate text-xs text-muted-foreground">
                      {user.email}
                    </p>
                  </div>
                  <div className="py-1">
                    <Link
                      href="/admin/account"
                      onClick={() => setMenuOpen(false)}
                      className="flex items-center gap-2.5 rounded-lg px-3 py-2 text-sm text-muted-foreground transition-colors hover:bg-secondary hover:text-foreground"
                    >
                      <UserCircle className="size-4" />
                      Account settings
                    </Link>
                    <Link
                      href="/admin/users"
                      onClick={() => setMenuOpen(false)}
                      className="flex items-center gap-2.5 rounded-lg px-3 py-2 text-sm text-muted-foreground transition-colors hover:bg-secondary hover:text-foreground"
                    >
                      <Users className="size-4" />
                      Users & roles
                    </Link>
                    <Link
                      href="/admin/settings"
                      onClick={() => setMenuOpen(false)}
                      className="flex items-center gap-2.5 rounded-lg px-3 py-2 text-sm text-muted-foreground transition-colors hover:bg-secondary hover:text-foreground"
                    >
                      <Settings className="size-4" />
                      Website settings
                    </Link>
                  </div>
                  <div className="border-t border-border pt-1">
                    <button
                      type="button"
                      onClick={signOut}
                      className="flex w-full cursor-pointer items-center gap-2.5 rounded-lg px-3 py-2 text-sm text-muted-foreground transition-colors hover:bg-secondary hover:text-foreground"
                    >
                      <LogOut className="size-4" />
                      Sign out
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        </header>

        <main className="flex-1 p-5 sm:p-8">{children}</main>
      </div>
    </div>
  );
}
