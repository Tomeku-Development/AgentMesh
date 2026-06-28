import Link from "next/link";
import { TwoFactorVerifyForm } from "./two-factor-verify-form";

export const dynamic = "force-dynamic";

export default function AdminTwoFactorPage() {
  return (
    <main className="flex min-h-screen items-center justify-center bg-background px-5 py-12">
      <div className="w-full max-w-md">
        <div className="mb-8 text-center">
          <p className="text-xs font-semibold uppercase tracking-[0.25em] text-brand">
            Admin security
          </p>
          <h1 className="mt-4 font-heading text-3xl font-bold text-foreground">
            Two-factor verification
          </h1>
          <p className="mt-2 text-sm text-muted-foreground">
            Enter the code from your authenticator app to finish signing in.
          </p>
        </div>

        <div className="rounded-xl border border-border bg-card p-6 shadow-2xl shadow-black/30">
          <TwoFactorVerifyForm />
        </div>

        <p className="mt-6 text-center text-sm text-muted-foreground">
          Wrong account?{" "}
          <Link href="/admin/login" className="text-brand hover:underline">
            Return to sign in
          </Link>
        </p>
      </div>
    </main>
  );
}
