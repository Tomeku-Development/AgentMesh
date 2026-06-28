"use client";

import { useActionState, useEffect, useRef } from "react";
import { useFormStatus } from "react-dom";
import { Check, Loader2 } from "lucide-react";
import {
  changeAccountPassword,
  updateAccountProfile,
  type SaveState,
} from "@/app/admin/actions";
import { cn } from "@/lib/utils";

const initialState: SaveState = { status: "idle", message: "" };

const fieldClass =
  "h-11 w-full rounded-md border border-border bg-background/60 px-4 text-sm text-foreground outline-none transition-colors placeholder:text-muted-foreground focus:border-brand/60 focus:ring-2 focus:ring-brand/30 disabled:cursor-not-allowed disabled:opacity-60";

function SaveButton({ label }: { label: string }) {
  const { pending } = useFormStatus();
  return (
    <button
      type="submit"
      disabled={pending}
      className="inline-flex h-10 cursor-pointer items-center justify-center gap-2 rounded-md bg-brand px-4 text-sm font-semibold text-primary-foreground transition-all hover:brightness-110 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand/50 disabled:cursor-not-allowed disabled:opacity-60"
    >
      {pending ? <Loader2 className="size-4 animate-spin" /> : label}
    </button>
  );
}

function StateMessage({ state }: { state: SaveState }) {
  if (state.status === "idle") return null;
  return (
    <p
      aria-live="polite"
      className={cn(
        "flex items-center gap-1.5 text-sm",
        state.status === "success" ? "text-success" : "text-destructive",
      )}
    >
      {state.status === "success" && <Check className="size-4" />}
      {state.message}
    </p>
  );
}

export function ProfileForm({
  name,
  email,
}: {
  name: string;
  email: string;
}) {
  const [state, formAction] = useActionState(updateAccountProfile, initialState);

  return (
    <form action={formAction} className="rounded-xl border border-border bg-card p-5">
      <div className="border-b border-border pb-4">
        <h2 className="font-heading text-sm font-semibold text-foreground">
          Profile
        </h2>
        <p className="mt-1 text-xs text-muted-foreground">
          This is shown in the admin header and activity surfaces.
        </p>
      </div>

      <div className="mt-5 grid grid-cols-1 gap-4 sm:grid-cols-2">
        <label className="flex flex-col gap-1.5">
          <span className="text-sm font-medium text-foreground">Name</span>
          <input
            name="name"
            defaultValue={name}
            required
            minLength={2}
            maxLength={120}
            className={fieldClass}
          />
        </label>
        <label className="flex flex-col gap-1.5">
          <span className="text-sm font-medium text-foreground">Email</span>
          <input value={email} disabled className={fieldClass} />
        </label>
      </div>

      <div className="mt-5 flex flex-wrap items-center gap-3">
        <SaveButton label="Save profile" />
        <StateMessage state={state} />
      </div>
    </form>
  );
}

export function PasswordForm() {
  const formRef = useRef<HTMLFormElement>(null);
  const [state, formAction] = useActionState(changeAccountPassword, initialState);

  useEffect(() => {
    if (state.status === "success") formRef.current?.reset();
  }, [state.status]);

  return (
    <form
      ref={formRef}
      action={formAction}
      className="rounded-xl border border-border bg-card p-5"
    >
      <div className="border-b border-border pb-4">
        <h2 className="font-heading text-sm font-semibold text-foreground">
          Security
        </h2>
        <p className="mt-1 text-xs text-muted-foreground">
          Change your password. You can also revoke other active sessions.
        </p>
      </div>

      <div className="mt-5 grid grid-cols-1 gap-4 sm:grid-cols-3">
        <label className="flex flex-col gap-1.5">
          <span className="text-sm font-medium text-foreground">
            Current password
          </span>
          <input
            name="currentPassword"
            type="password"
            autoComplete="current-password"
            required
            className={fieldClass}
          />
        </label>
        <label className="flex flex-col gap-1.5">
          <span className="text-sm font-medium text-foreground">
            New password
          </span>
          <input
            name="newPassword"
            type="password"
            autoComplete="new-password"
            required
            minLength={8}
            className={fieldClass}
          />
        </label>
        <label className="flex flex-col gap-1.5">
          <span className="text-sm font-medium text-foreground">
            Confirm password
          </span>
          <input
            name="confirmPassword"
            type="password"
            autoComplete="new-password"
            required
            minLength={8}
            className={fieldClass}
          />
        </label>
      </div>

      <label className="mt-4 flex items-center gap-2 text-sm text-muted-foreground">
        <input
          type="checkbox"
          name="revokeOtherSessions"
          className="size-4 rounded border-border bg-background accent-brand"
        />
        Sign out other sessions after changing password
      </label>

      <div className="mt-5 flex flex-wrap items-center gap-3">
        <SaveButton label="Update password" />
        <StateMessage state={state} />
      </div>
    </form>
  );
}
