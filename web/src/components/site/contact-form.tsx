"use client";

import { useActionState } from "react";
import { useFormStatus } from "react-dom";
import { Loader2, Check, ArrowRight } from "lucide-react";
import { submitContact, type ContactState } from "@/app/actions/contact";
import { cn } from "@/lib/utils";

const initialState: ContactState = { status: "idle", message: "" };

const fieldClass =
  "h-11 w-full rounded-md border border-border bg-background/60 px-4 text-sm text-foreground outline-none transition-colors placeholder:text-muted-foreground focus:border-brand/60 focus:ring-2 focus:ring-brand/30";

function SubmitButton() {
  const { pending } = useFormStatus();
  return (
    <button
      type="submit"
      disabled={pending}
      className="inline-flex h-11 cursor-pointer items-center justify-center gap-2 rounded-md bg-brand px-6 text-sm font-semibold text-primary-foreground transition-all hover:brightness-110 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand/50 disabled:cursor-not-allowed disabled:opacity-60"
    >
      {pending ? (
        <Loader2 className="size-4 animate-spin" />
      ) : (
        <>
          Send message
          <ArrowRight className="size-4" />
        </>
      )}
    </button>
  );
}

export function ContactForm() {
  const [state, formAction] = useActionState(submitContact, initialState);

  if (state.status === "success") {
    return (
      <div className="flex flex-col items-start gap-3 rounded-xl border border-brand/30 bg-brand/10 p-6">
        <span className="inline-flex size-10 items-center justify-center rounded-full bg-brand/20 text-brand">
          <Check className="size-5" />
        </span>
        <h3 className="font-heading text-lg font-semibold text-foreground">
          Message sent
        </h3>
        <p className="text-sm text-muted-foreground">{state.message}</p>
      </div>
    );
  }

  return (
    <form action={formAction} className="flex flex-col gap-4" noValidate>
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <div className="flex flex-col gap-1.5">
          <label htmlFor="name" className="text-sm font-medium text-foreground">
            Name
          </label>
          <input
            id="name"
            name="name"
            type="text"
            autoComplete="name"
            placeholder="Jane Doe"
            className={fieldClass}
            aria-invalid={Boolean(state.errors?.name)}
          />
          {state.errors?.name && (
            <span className="text-xs text-destructive">
              {state.errors.name}
            </span>
          )}
        </div>

        <div className="flex flex-col gap-1.5">
          <label
            htmlFor="email"
            className="text-sm font-medium text-foreground"
          >
            Email
          </label>
          <input
            id="email"
            name="email"
            type="email"
            autoComplete="email"
            placeholder="you@company.com"
            className={fieldClass}
            aria-invalid={Boolean(state.errors?.email)}
          />
          {state.errors?.email && (
            <span className="text-xs text-destructive">
              {state.errors.email}
            </span>
          )}
        </div>
      </div>

      <div className="flex flex-col gap-1.5">
        <label htmlFor="company" className="text-sm font-medium text-foreground">
          Company <span className="text-muted-foreground">(optional)</span>
        </label>
        <input
          id="company"
          name="company"
          type="text"
          autoComplete="organization"
          placeholder="Acme Inc."
          className={fieldClass}
        />
      </div>

      <div className="flex flex-col gap-1.5">
        <label
          htmlFor="message"
          className="text-sm font-medium text-foreground"
        >
          Message
        </label>
        <textarea
          id="message"
          name="message"
          rows={5}
          placeholder="Tell us what you're building…"
          className={cn(fieldClass, "h-auto py-3 leading-relaxed")}
          aria-invalid={Boolean(state.errors?.message)}
        />
        {state.errors?.message && (
          <span className="text-xs text-destructive">
            {state.errors.message}
          </span>
        )}
      </div>

      {state.status === "error" && !state.errors && (
        <p className="text-sm text-destructive" aria-live="polite">
          {state.message}
        </p>
      )}

      <div>
        <SubmitButton />
      </div>
    </form>
  );
}
