"use client";

import { useActionState } from "react";
import { useFormStatus } from "react-dom";
import { Loader2, Check, Save } from "lucide-react";
import { saveContent, type SaveState } from "@/app/admin/actions";
import type { ContentField, SiteContentMap } from "@/lib/data/site-content";
import { cn } from "@/lib/utils";

const initial: SaveState = { status: "idle", message: "" };

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
          Save changes
        </>
      )}
    </button>
  );
}

const fieldClass =
  "w-full rounded-md border border-border bg-background/60 px-4 py-2.5 text-sm text-foreground outline-none transition-colors placeholder:text-muted-foreground focus:border-brand/60 focus:ring-2 focus:ring-brand/30";

export function ContentForm({
  fields,
  values,
}: {
  fields: ContentField[];
  values: SiteContentMap;
}) {
  const [state, formAction] = useActionState(saveContent, initial);

  const groups = Array.from(new Set(fields.map((f) => f.group)));

  return (
    <form action={formAction} className="flex flex-col gap-8">
      {groups.map((group) => (
        <fieldset
          key={group}
          className="rounded-xl border border-border bg-card p-6"
        >
          <legend className="px-2 font-heading text-sm font-semibold text-foreground">
            {group}
          </legend>
          <div className="mt-2 flex flex-col gap-5">
            {fields
              .filter((f) => f.group === group)
              .map((field) => (
                <div key={field.key} className="flex flex-col gap-1.5">
                  <label
                    htmlFor={field.key}
                    className="text-sm font-medium text-foreground"
                  >
                    {field.label}
                  </label>
                  {field.multiline ? (
                    <textarea
                      id={field.key}
                      name={field.key}
                      defaultValue={values[field.key] ?? field.default}
                      rows={3}
                      className={cn(fieldClass, "leading-relaxed")}
                    />
                  ) : (
                    <input
                      id={field.key}
                      name={field.key}
                      type="text"
                      defaultValue={values[field.key] ?? field.default}
                      className={fieldClass}
                    />
                  )}
                </div>
              ))}
          </div>
        </fieldset>
      ))}

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
