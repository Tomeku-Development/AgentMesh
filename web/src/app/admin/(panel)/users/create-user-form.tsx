"use client";

import { useActionState, useEffect, useRef } from "react";
import { useFormStatus } from "react-dom";
import { Loader2, UserPlus, Check } from "lucide-react";
import { createUserAction, type SaveState } from "@/app/admin/actions";
import { cn } from "@/lib/utils";

const initial: SaveState = { status: "idle", message: "" };
const fieldClass =
  "h-10 w-full rounded-md border border-border bg-background/60 px-3 text-sm text-foreground outline-none transition-colors placeholder:text-muted-foreground focus:border-brand/60 focus:ring-2 focus:ring-brand/30";

function SubmitButton() {
  const { pending } = useFormStatus();
  return (
    <button
      type="submit"
      disabled={pending}
      className="inline-flex h-10 cursor-pointer items-center justify-center gap-2 rounded-md bg-brand px-4 text-sm font-semibold text-primary-foreground transition-all hover:brightness-110 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand/50 disabled:cursor-not-allowed disabled:opacity-60"
    >
      {pending ? (
        <Loader2 className="size-4 animate-spin" />
      ) : (
        <>
          <UserPlus className="size-4" />
          Create user
        </>
      )}
    </button>
  );
}

export function CreateUserForm() {
  const [state, formAction] = useActionState(createUserAction, initial);
  const formRef = useRef<HTMLFormElement>(null);

  useEffect(() => {
    if (state.status === "success") formRef.current?.reset();
  }, [state]);

  return (
    <form
      ref={formRef}
      action={formAction}
      className="rounded-xl border border-border bg-card p-5"
    >
      <h2 className="font-heading text-sm font-semibold text-foreground">
        Invite a user
      </h2>
      <p className="mt-1 text-xs text-muted-foreground">
        Creates an account with a temporary password you set. Share it securely.
      </p>
      <div className="mt-4 grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <input name="name" placeholder="Name" required className={fieldClass} />
        <input
          name="email"
          type="email"
          placeholder="email@company.com"
          required
          className={fieldClass}
        />
        <input
          name="password"
          type="password"
          placeholder="Temp password (8+)"
          required
          minLength={8}
          className={fieldClass}
        />
        <select name="role" defaultValue="user" className={fieldClass}>
          <option value="user">User</option>
          <option value="admin">Admin</option>
        </select>
      </div>
      <div className="mt-4 flex items-center gap-3">
        <SubmitButton />
        {state.status !== "idle" && (
          <span
            className={cn(
              "flex items-center gap-1.5 text-sm",
              state.status === "success" ? "text-success" : "text-destructive",
            )}
            aria-live="polite"
          >
            {state.status === "success" && <Check className="size-4" />}
            {state.message}
          </span>
        )}
      </div>
    </form>
  );
}
