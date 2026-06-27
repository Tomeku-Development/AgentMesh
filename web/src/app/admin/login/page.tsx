import type { Metadata } from "next";
import { Logo } from "@/components/site/logo";
import { userCount } from "@/lib/session";
import { LoginForm } from "./login-form";

export const metadata: Metadata = {
  title: "Admin — Sign in",
  robots: { index: false, follow: false },
};

export const dynamic = "force-dynamic";

export default async function AdminLoginPage({
  searchParams,
}: {
  searchParams: Promise<{ next?: string; error?: string }>;
}) {
  const { next, error } = await searchParams;
  const users = await userCount();
  const mode = users === 0 ? "bootstrap" : "signin";

  return (
    <main className="flex min-h-screen items-center justify-center px-5">
      <div className="w-full max-w-sm">
        <div className="mb-8 flex flex-col items-center gap-4 text-center">
          <Logo />
          <div>
            <h1 className="font-heading text-xl font-semibold text-foreground">
              {mode === "bootstrap" ? "Create the first admin" : "Admin access"}
            </h1>
            <p className="mt-1 text-sm text-muted-foreground">
              {mode === "bootstrap"
                ? "Set up the owner account for your workspace."
                : "Sign in to manage content, media, and users."}
            </p>
          </div>
        </div>
        <div className="rounded-2xl border border-border bg-card p-6 sm:p-7">
          <LoginForm
            mode={mode}
            next={next ?? "/admin"}
            initialError={error}
          />
        </div>
        <p className="mt-6 text-center text-xs text-muted-foreground">
          Authorized personnel only.
        </p>
      </div>
    </main>
  );
}
