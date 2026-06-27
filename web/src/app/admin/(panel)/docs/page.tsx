import Link from "next/link";
import { Plus, Pencil, Trash2, Eye, EyeOff, BookText } from "lucide-react";
import { getAllDocsAdmin, groupByCategory } from "@/lib/data/docs";
import { isDatabaseConfigured } from "@/lib/db";
import { deleteDoc, toggleDocPublished } from "@/app/admin/actions";
import { cn } from "@/lib/utils";

export const dynamic = "force-dynamic";

export default async function AdminDocsPage() {
  const docs = await getAllDocsAdmin();
  const groups = groupByCategory(docs);

  return (
    <div className="mx-auto max-w-5xl">
      <header className="mb-8 flex items-end justify-between gap-4">
        <div>
          <h1 className="font-heading text-2xl font-bold text-foreground">
            Documentation
          </h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Write and publish docs. {docs.length} page
            {docs.length === 1 ? "" : "s"}.
          </p>
        </div>
        <Link
          href="/admin/docs/new"
          className="inline-flex h-10 shrink-0 items-center gap-2 rounded-md bg-brand px-4 text-sm font-semibold text-primary-foreground transition-all hover:brightness-110"
        >
          <Plus className="size-4" />
          New document
        </Link>
      </header>

      {!isDatabaseConfigured && (
        <div className="mb-6 rounded-xl border border-warning/30 bg-warning/10 p-4 text-sm text-warning">
          Database not configured. Set <code>DATABASE_URL</code> to manage docs.
        </div>
      )}

      {docs.length === 0 ? (
        <div className="flex flex-col items-center gap-3 rounded-xl border border-dashed border-border p-12 text-center">
          <BookText className="size-8 text-muted-foreground" />
          <p className="text-sm text-muted-foreground">
            No documents yet. Create your first doc to populate{" "}
            <code>/docs</code>.
          </p>
          <Link
            href="/admin/docs/new"
            className="mt-1 inline-flex h-9 items-center gap-2 rounded-md bg-brand px-4 text-sm font-semibold text-primary-foreground hover:brightness-110"
          >
            <Plus className="size-4" />
            New document
          </Link>
        </div>
      ) : (
        <div className="flex flex-col gap-6">
          {groups.map((group) => (
            <div key={group.category}>
              <h2 className="mb-2 text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
                {group.category}
              </h2>
              <div className="overflow-hidden rounded-xl border border-border">
                {group.docs.map((doc, i) => (
                  <div
                    key={doc.id}
                    className={cn(
                      "flex items-center gap-3 bg-card px-5 py-3.5",
                      i !== 0 && "border-t border-border",
                    )}
                  >
                    <div className="min-w-0 flex-1">
                      <Link
                        href={`/admin/docs/${doc.id}`}
                        className="truncate text-sm font-medium text-foreground hover:text-brand"
                      >
                        {doc.title}
                      </Link>
                      <p className="truncate text-xs text-muted-foreground">
                        /docs/{doc.slug}
                      </p>
                    </div>

                    <span
                      className={cn(
                        "hidden rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider sm:inline",
                        doc.published
                          ? "bg-success/15 text-success"
                          : "bg-secondary text-muted-foreground",
                      )}
                    >
                      {doc.published ? "Published" : "Draft"}
                    </span>

                    <form action={toggleDocPublished}>
                      <input type="hidden" name="id" value={doc.id} />
                      <input
                        type="hidden"
                        name="publish"
                        value={doc.published ? "0" : "1"}
                      />
                      <button
                        type="submit"
                        title={doc.published ? "Unpublish" : "Publish"}
                        className="inline-flex size-8 items-center justify-center rounded-md border border-border text-muted-foreground transition-colors hover:bg-secondary hover:text-foreground"
                      >
                        {doc.published ? (
                          <EyeOff className="size-3.5" />
                        ) : (
                          <Eye className="size-3.5" />
                        )}
                      </button>
                    </form>

                    <Link
                      href={`/admin/docs/${doc.id}`}
                      title="Edit"
                      className="inline-flex size-8 items-center justify-center rounded-md border border-border text-muted-foreground transition-colors hover:bg-secondary hover:text-foreground"
                    >
                      <Pencil className="size-3.5" />
                    </Link>

                    <form action={deleteDoc}>
                      <input type="hidden" name="id" value={doc.id} />
                      <button
                        type="submit"
                        title="Delete"
                        className="inline-flex size-8 items-center justify-center rounded-md border border-border text-muted-foreground transition-colors hover:border-destructive/40 hover:bg-destructive/10 hover:text-destructive"
                      >
                        <Trash2 className="size-3.5" />
                      </button>
                    </form>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
