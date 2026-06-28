"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Fingerprint, Loader2 } from "lucide-react";
import { authClient } from "@/lib/auth-client";

const fieldClass =
  "h-11 w-full rounded-md border border-border bg-background/60 px-4 text-sm text-foreground outline-none transition-colors placeholder:text-muted-foreground focus:border-brand/60 focus:ring-2 focus:ring-brand/30";

export function LoginForm({
  mode,
  next,
  initialError,
}: {
  mode: "signin" | "bootstrap";
  next: string;
  initialError?: string;
}) {
  const router = useRouter();
  const [pending, setPending] = useState(false);
  const [passkeyPending, setPasskeyPending] = useState(false);
  const [error, setError] = useState<string | null>(
    initialError === "forbidden"
      ? "That account doesn't have admin access."
      : null,
  );

  async function onSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setError(null);
    const form = new FormData(e.currentTarget);
    const email = String(form.get("email") ?? "").trim();
    const password = String(form.get("password") ?? "");
    const name = String(form.get("name") ?? "").trim();

    setPending(true);
    try {
      if (mode === "bootstrap") {
        const { error } = await authClient.signUp.email({
          email,
          password,
          name,
        });
        if (error) {
          setError(error.message ?? "Could not create account.");
          return;
        }
      } else {
        const { error } = await authClient.signIn.email({ email, password });
        if (error) {
          setError(error.message ?? "Invalid email or password.");
          return;
        }
      }
      router.push(next);
      router.refresh();
    } catch {
      setError("Something went wrong. Please try again.");
    } finally {
      setPending(false);
    }
  }

  async function signInWithPasskey() {
    setPasskeyPending(true);
    setError(null);
    try {
      const { error } = await authClient.signIn.passkey();
      if (error) {
        setError(error.message ?? "Could not sign in with passkey.");
        return;
      }
      router.push(next);
      router.refresh();
    } catch {
      setError("Passkey sign-in was canceled or failed.");
    } finally {
      setPasskeyPending(false);
    }
  }

  return (
    <form onSubmit={onSubmit} className="flex flex-col gap-4">
      {mode === "bootstrap" && (
        <div className="flex flex-col gap-1.5">
          <label htmlFor="name" className="text-sm font-medium text-foreground">
            Your name
          </label>
          <input
            id="name"
            name="name"
            type="text"
            autoComplete="name"
            required
            placeholder="Jane Doe"
            className={fieldClass}
          />
        </div>
      )}
      <div className="flex flex-col gap-1.5">
        <label htmlFor="email" className="text-sm font-medium text-foreground">
          Email
        </label>
        <input
          id="email"
          name="email"
          type="email"
          autoComplete="email"
          required
          placeholder="you@company.com"
          className={fieldClass}
        />
      </div>
      <div className="flex flex-col gap-1.5">
        <label
          htmlFor="password"
          className="text-sm font-medium text-foreground"
        >
          Password
        </label>
        <input
          id="password"
          name="password"
          type="password"
          autoComplete={mode === "bootstrap" ? "new-password" : "current-password"}
          required
          minLength={8}
          placeholder="••••••••"
          className={fieldClass}
        />
      </div>

      {error && (
        <p className="text-sm text-destructive" aria-live="polite">
          {error}
        </p>
      )}

      <button
        type="submit"
        disabled={pending || passkeyPending}
        className="inline-flex h-11 w-full cursor-pointer items-center justify-center gap-2 rounded-md bg-brand text-sm font-semibold text-primary-foreground transition-all hover:brightness-110 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand/50 disabled:cursor-not-allowed disabled:opacity-60"
      >
        {pending ? (
          <Loader2 className="size-4 animate-spin" />
        ) : mode === "bootstrap" ? (
          "Create admin account"
        ) : (
          "Sign in"
        )}
      </button>

      {mode === "signin" && (
        <button
          type="button"
          onClick={signInWithPasskey}
          disabled={pending || passkeyPending}
          className="inline-flex h-11 w-full cursor-pointer items-center justify-center gap-2 rounded-md border border-border bg-card text-sm font-semibold text-foreground transition-colors hover:bg-secondary disabled:cursor-not-allowed disabled:opacity-60"
        >
          {passkeyPending ? (
            <Loader2 className="size-4 animate-spin" />
          ) : (
            <Fingerprint className="size-4" />
          )}
          Sign in with passkey
        </button>
      )}
    </form>
  );
}
