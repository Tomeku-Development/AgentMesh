"use client";

import { useActionState } from "react";
import { useFormStatus } from "react-dom";
import Link from "next/link";
import { Loader2, Save, ArrowLeft } from "lucide-react";
import { saveDoc, type SaveState } from "@/app/admin/actions";
import type { DocPage } from "@/lib/db/schema";

const initial: SaveState = { status: "idle", message: "" };
const fieldClass =
  "w-full rounded-md border border-border bg-background/60 px-3 py-2.5 text-sm text-foreground outline-none transition-colors placeholder:text-muted-foreground focus:border-brand/60 focus:ring-2 focus:ring-brand/30";

function SaveButton() {
  const { pending } = useFormStatus();
  return (
    <button
      type="submit"
      disabled={pending}
      className="inline-flex h-10 cursor-pointer items-center justify-center gap-2 rounded-md bg-brand px-5 text-sm font-semibold text-primary-foreground transition-all hover:brightness-110 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand/50 disabled:cursor-not-allowed disabled:opacity-60"
    >
      {pending ? <Loader2 className="size-4 animate-spin" /> : <Save className="size-4" />}
      Save document
    </button>
  );
}

function Field({
  label,
  children,
  hint,
}: {
  label: string;
  children: React.ReactNode;
  hint?: string;
}) {
  return (
    <label className="flex flex-col gap-1.5">
      <span className="text-sm font-medium text-foreground">{label}</span>
      {children}
      {hint && <span className="text-xs text-muted-foreground">{hint}</span>}
    </label>
  );
}

export function DocEditor({ doc }: { doc?: DocPage }) {
  const [state, formAction] = useActionState(saveDoc, initial);

  return (
    <form action={formAction} className="flex flex-col gap-6">
      {doc && <input type="hidden" name="id" value={doc.id} />}

      <div className="flex items-center justify-between">
        <Link
          href="/admin/docs"
          className="inline-flex items-center gap-1.5 text-sm text-muted-foreground transition-colors hover:text-foreground"
        >
          <ArrowLeft className="size-4" />
          Back to docs
        </Link>
        <SaveButton />
      </div>

      {state.status === "error" && (
        <p className="rounded-lg border border-destructive/30 bg-destructive/10 p-3 text-sm text-destructive">
          {state.message}
        </p>
      )}

      <div className="grid grid-cols-1 gap-5 lg:grid-cols-3">
        {/* Main */}
        <div className="flex flex-col gap-5 lg:col-span-2">
          <div className="rounded-xl border border-border bg-card p-5">
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <Field label="Title">
                <input
                  name="title"
                  required
                  defaultValue={doc?.title ?? ""}
                  placeholder="Getting started"
                  className={fieldClass}
                />
              </Field>
              <Field label="Slug" hint="URL: /docs/your-slug">
                <input
                  name="slug"
                  defaultValue={doc?.slug ?? ""}
                  placeholder="getting-started"
                  className={fieldClass}
                />
              </Field>
            </div>
            <div className="mt-4">
              <Field label="Summary" hint="Shown in the docs index.">
                <input
                  name="summary"
                  defaultValue={doc?.summary ?? ""}
                  placeholder="A short one-line description."
                  className={fieldClass}
                />
              </Field>
            </div>
            <div className="mt-4">
              <Field label="Body (Markdown)">
                <textarea
                  name="body"
                  defaultValue={doc?.body ?? ""}
                  rows={20}
                  placeholder={"# Heading\n\nWrite your documentation in Markdown..."}
                  className={`${fieldClass} font-mono text-[13px] leading-relaxed`}
                />
              </Field>
            </div>
          </div>
        </div>

        {/* Sidebar */}
        <div className="flex flex-col gap-5">
          <div className="rounded-xl border border-border bg-card p-5">
            <h3 className="font-heading text-sm font-semibold text-foreground">
              Organization
            </h3>
            <div className="mt-4 flex flex-col gap-4">
              <Field label="Category">
                <input
                  name="category"
                  defaultValue={doc?.category ?? "General"}
                  placeholder="General"
                  className={fieldClass}
                />
              </Field>
              <Field label="Sort order" hint="Lower shows first.">
                <input
                  name="sortOrder"
                  type="number"
                  defaultValue={doc?.sortOrder ?? 0}
                  className={fieldClass}
                />
              </Field>
              <label className="flex items-center gap-2.5">
                <input
                  type="checkbox"
                  name="published"
                  defaultChecked={doc?.published ?? false}
                  className="size-4 accent-[var(--brand)]"
                />
                <span className="text-sm text-foreground">Published</span>
              </label>
            </div>
          </div>

          <div className="rounded-xl border border-border bg-card p-5">
            <h3 className="font-heading text-sm font-semibold text-foreground">
              SEO metadata
            </h3>
            <div className="mt-4 flex flex-col gap-4">
              <Field label="SEO title" hint="Defaults to the title.">
                <input
                  name="seoTitle"
                  defaultValue={doc?.seoTitle ?? ""}
                  className={fieldClass}
                />
              </Field>
              <Field label="Meta description">
                <textarea
                  name="seoDescription"
                  defaultValue={doc?.seoDescription ?? ""}
                  rows={3}
                  className={`${fieldClass} leading-relaxed`}
                />
              </Field>
            </div>
          </div>
        </div>
      </div>
    </form>
  );
}
