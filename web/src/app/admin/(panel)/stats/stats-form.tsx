"use client";

import { useActionState } from "react";
import { useFormStatus } from "react-dom";
import { Loader2, Check, Save } from "lucide-react";
import { saveStats, type SaveState } from "@/app/admin/actions";
import { cn } from "@/lib/utils";

const initial: SaveState = { status: "idle", message: "" };

const fields = [
  { name: "agentsOnline", label: "Agents Online" },
  { name: "transactions", label: "Transactions" },
  { name: "proposals", label: "Proposals" },
  { name: "tvlCspr", label: "TVL on Casper (CSPR)" },
] as const;

function SaveButton() {
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
          <Save className="size-4" />
          Update stats
        </>
      )}
    </button>
  );
}

export function StatsForm({
  values,
}: {
  values: Record<(typeof fields)[number]["name"], number>;
}) {
  const [state, formAction] = useActionState(saveStats, initial);

  return (
    <form action={formAction} className="flex flex-col gap-6">
      <div className="grid grid-cols-1 gap-5 rounded-xl border border-border bg-card p-6 sm:grid-cols-2">
        {fields.map((field) => (
          <div key={field.name} className="flex flex-col gap-1.5">
            <label
              htmlFor={field.name}
              className="text-sm font-medium text-foreground"
            >
              {field.label}
            </label>
            <input
              id={field.name}
              name={field.name}
              type="number"
              min={0}
              step={1}
              defaultValue={values[field.name]}
              className="h-11 w-full rounded-md border border-border bg-background/60 px-4 font-mono text-sm text-foreground outline-none transition-colors focus:border-brand/60 focus:ring-2 focus:ring-brand/30"
            />
          </div>
        ))}
      </div>

      <div className="flex items-center gap-4">
        <SaveButton />
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
