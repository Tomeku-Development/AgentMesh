"use client";

import { useActionState, useEffect, useRef } from "react";
import { useFormStatus } from "react-dom";
import { ArrowRight, Loader2, Check } from "lucide-react";
import { subscribe, type SubscribeState } from "@/app/actions/subscribe";
import { trackEvent } from "@/lib/analytics";
import { cn } from "@/lib/utils";

const initialState: SubscribeState = { status: "idle", message: "" };

function SubmitButton() {
  const { pending } = useFormStatus();
  return (
    <button
      type="submit"
      disabled={pending}
      className="inline-flex h-11 cursor-pointer items-center justify-center gap-2 whitespace-nowrap rounded-md bg-brand px-5 text-sm font-semibold text-primary-foreground transition-all hover:brightness-110 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand/50 disabled:cursor-not-allowed disabled:opacity-60"
    >
      {pending ? (
        <Loader2 className="size-4 animate-spin" />
      ) : (
        <>
          Get Early Access
          <ArrowRight className="size-4" />
        </>
      )}
    </button>
  );
}

export function SubscribeForm() {
  const [state, formAction] = useActionState(subscribe, initialState);
  const lastStatusRef = useRef(state.status);

  useEffect(() => {
    if (state.status === "idle" || lastStatusRef.current === state.status) {
      return;
    }
    lastStatusRef.current = state.status;

    trackEvent(
      state.status === "success"
        ? "newsletter_signup_completed"
        : "newsletter_signup_failed",
      {
        form_name: "newsletter",
        page_path: window.location.pathname,
      },
    );
  }, [state.status]);

  return (
    <div className="w-full max-w-md">
      <form
        action={formAction}
        data-analytics-form="newsletter"
        className="flex flex-col gap-3 sm:flex-row sm:items-center"
      >
        <input
          type="email"
          name="email"
          required
          autoComplete="email"
          placeholder="you@company.com"
          aria-label="Email address"
          className="h-11 flex-1 rounded-md border border-border bg-background/60 px-4 text-sm text-foreground outline-none transition-colors placeholder:text-muted-foreground focus:border-brand/60 focus:ring-2 focus:ring-brand/30"
        />
        <SubmitButton />
      </form>

      {state.status !== "idle" && (
        <p
          aria-live="polite"
          className={cn(
            "mt-3 flex items-center gap-1.5 text-sm",
            state.status === "success" ? "text-brand" : "text-destructive",
          )}
        >
          {state.status === "success" && <Check className="size-4" />}
          {state.message}
        </p>
      )}
    </div>
  );
}
