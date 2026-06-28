import { ShieldCheck, UserCircle } from "lucide-react";
import { getSession } from "@/lib/session";
import { ProfileForm, PasswordForm } from "./account-forms";
import { ApiKeyCard } from "./api-key-card";
import { PasskeyCard } from "./passkey-card";
import { TwoFactorCard } from "./two-factor-card";

export const dynamic = "force-dynamic";

const fmt = new Intl.DateTimeFormat("en-US", {
  dateStyle: "medium",
  timeStyle: "short",
});

export default async function AdminAccountPage() {
  const session = await getSession();
  if (!session) return null;
  const accountUser = session.user as typeof session.user & {
    lastLoginMethod?: string | null;
    role?: string | null;
    twoFactorEnabled?: boolean;
  };
  const twoFactorEnabled = Boolean(accountUser.twoFactorEnabled);
  const lastLoginMethod = accountUser.lastLoginMethod ?? "Not recorded";

  return (
    <div className="mx-auto max-w-5xl">
      <header className="mb-8">
        <h1 className="font-heading text-2xl font-bold text-foreground">
          Account Settings
        </h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Manage your profile, password, and current admin session.
        </p>
      </header>

      <div className="mb-6 rounded-xl border border-border bg-card p-5">
        <div className="flex flex-wrap items-center gap-4">
          <span className="flex size-14 items-center justify-center rounded-full bg-brand/15 text-lg font-bold text-brand">
            {session.user.name
              .split(" ")
              .map((part) => part[0])
              .filter(Boolean)
              .slice(0, 2)
              .join("")
              .toUpperCase() || "AM"}
          </span>
          <div className="min-w-0 flex-1">
            <p className="truncate font-heading text-lg font-semibold text-foreground">
              {session.user.name}
            </p>
            <p className="truncate text-sm text-muted-foreground">
              {session.user.email}
            </p>
          </div>
          <span className="inline-flex items-center gap-1.5 rounded-full bg-brand/15 px-3 py-1 text-xs font-semibold uppercase tracking-wider text-brand">
            <ShieldCheck className="size-3.5" />
            {accountUser.role ?? "user"}
          </span>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-6">
        <ProfileForm name={session.user.name} email={session.user.email} />
        <PasswordForm />
        <TwoFactorCard enabled={twoFactorEnabled} />
        <PasskeyCard />
        <ApiKeyCard />

        <section className="rounded-xl border border-border bg-card p-5">
          <div className="flex items-center gap-2 border-b border-border pb-4">
            <UserCircle className="size-4 text-brand" />
            <h2 className="font-heading text-sm font-semibold text-foreground">
              Current session
            </h2>
          </div>
          <dl className="mt-5 grid grid-cols-1 gap-4 text-sm sm:grid-cols-2">
            <div>
              <dt className="text-xs uppercase tracking-wider text-muted-foreground">
                Session created
              </dt>
              <dd className="mt-1 text-foreground">
                {fmt.format(new Date(session.session.createdAt))}
              </dd>
            </div>
            <div>
              <dt className="text-xs uppercase tracking-wider text-muted-foreground">
                Expires
              </dt>
              <dd className="mt-1 text-foreground">
                {fmt.format(new Date(session.session.expiresAt))}
              </dd>
            </div>
            <div>
              <dt className="text-xs uppercase tracking-wider text-muted-foreground">
                IP address
              </dt>
              <dd className="mt-1 text-foreground">
                {session.session.ipAddress ?? "Not recorded"}
              </dd>
            </div>
            <div>
              <dt className="text-xs uppercase tracking-wider text-muted-foreground">
                Last login method
              </dt>
              <dd className="mt-1 capitalize text-foreground">
                {lastLoginMethod}
              </dd>
            </div>
            <div>
              <dt className="text-xs uppercase tracking-wider text-muted-foreground">
                User agent
              </dt>
              <dd className="mt-1 truncate text-foreground">
                {session.session.userAgent ?? "Not recorded"}
              </dd>
            </div>
          </dl>
        </section>
      </div>
    </div>
  );
}
