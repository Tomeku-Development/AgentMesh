import type { Metadata } from "next";
import { cookies } from "next/headers";
import { getSiteContent } from "@/lib/data/site-content";
import { requireAdmin } from "@/lib/session";
import { AdminShell } from "./admin-shell";

export const metadata: Metadata = {
  title: "Admin — AgentMesh",
  robots: { index: false, follow: false },
};

export default async function AdminPanelLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const [session, c, cookieStore] = await Promise.all([
    requireAdmin(),
    getSiteContent(),
    cookies(),
  ]);

  const workspace = `${c["settings.site_name"]} HQ`;
  const initialCollapsed = cookieStore.get("am_admin_collapsed")?.value === "1";

  return (
    <AdminShell
      workspace={workspace}
      user={{
        name: session.user.name,
        email: session.user.email,
        role: (session.user.role as string) ?? "user",
      }}
      initialCollapsed={initialCollapsed}
    >
      {children}
    </AdminShell>
  );
}
