import { Download } from "lucide-react";
import { getSubscribers } from "@/lib/data/admin";
import { isDatabaseConfigured } from "@/lib/db";

export const dynamic = "force-dynamic";

const fmt = new Intl.DateTimeFormat("en-US", {
  dateStyle: "medium",
  timeStyle: "short",
});

export default async function AdminSubscribersPage() {
  const rows = await getSubscribers();

  return (
    <div className="mx-auto max-w-3xl">
      <header className="mb-8 flex items-end justify-between gap-4">
        <div>
          <h1 className="font-heading text-2xl font-bold text-foreground">
            Subscribers
          </h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Early-access signups from the homepage. {rows.length} total.
          </p>
        </div>
        {rows.length > 0 && (
          <a
            href="/api/admin/export/subscribers"
            className="inline-flex h-10 shrink-0 items-center gap-2 rounded-md border border-border bg-card px-4 text-sm font-medium text-foreground transition-colors hover:bg-secondary"
          >
            <Download className="size-4" />
            Export CSV
          </a>
        )}
      </header>

      {!isDatabaseConfigured ? (
        <Empty text="Database not configured. Set DATABASE_URL to capture signups." />
      ) : rows.length === 0 ? (
        <Empty text="No subscribers yet." />
      ) : (
        <div className="overflow-hidden rounded-xl border border-border">
          {rows.map((row, i) => (
            <div
              key={row.id}
              className={`flex items-center justify-between gap-4 bg-card p-4 ${
                i !== 0 ? "border-t border-border" : ""
              }`}
            >
              <span className="truncate text-sm text-foreground">
                {row.email}
              </span>
              <time className="shrink-0 text-xs text-muted-foreground">
                {fmt.format(new Date(row.createdAt))}
              </time>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function Empty({ text }: { text: string }) {
  return (
    <div className="rounded-xl border border-dashed border-border p-12 text-center text-sm text-muted-foreground">
      {text}
    </div>
  );
}
