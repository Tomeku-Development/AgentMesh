import { Download } from "lucide-react";
import { getContactSubmissions } from "@/lib/data/admin";
import { isDatabaseConfigured } from "@/lib/db";

export const dynamic = "force-dynamic";

const fmt = new Intl.DateTimeFormat("en-US", {
  dateStyle: "medium",
  timeStyle: "short",
});

export default async function AdminMessagesPage() {
  const rows = await getContactSubmissions();

  return (
    <div className="mx-auto max-w-3xl">
      <header className="mb-8 flex items-end justify-between gap-4">
        <div>
          <h1 className="font-heading text-2xl font-bold text-foreground">
            Messages
          </h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Contact form submissions. {rows.length} total.
          </p>
        </div>
        {rows.length > 0 && (
          <a
            href="/api/admin/export/contacts"
            className="inline-flex h-10 shrink-0 items-center gap-2 rounded-md border border-border bg-card px-4 text-sm font-medium text-foreground transition-colors hover:bg-secondary"
          >
            <Download className="size-4" />
            Export CSV
          </a>
        )}
      </header>

      {!isDatabaseConfigured ? (
        <Empty text="Database not configured. Set DATABASE_URL to capture messages." />
      ) : rows.length === 0 ? (
        <Empty text="No messages yet." />
      ) : (
        <div className="flex flex-col gap-4">
          {rows.map((row) => (
            <article
              key={row.id}
              className="rounded-xl border border-border bg-card p-5"
            >
              <div className="flex flex-wrap items-center justify-between gap-2">
                <div className="flex items-center gap-2">
                  <span className="font-medium text-foreground">{row.name}</span>
                  {row.company && (
                    <span className="rounded-full bg-secondary px-2 py-0.5 text-[11px] text-muted-foreground">
                      {row.company}
                    </span>
                  )}
                </div>
                <time className="text-xs text-muted-foreground">
                  {fmt.format(new Date(row.createdAt))}
                </time>
              </div>
              <a
                href={`mailto:${row.email}`}
                className="mt-1 inline-block text-sm text-brand underline-offset-4 hover:underline"
              >
                {row.email}
              </a>
              <p className="mt-3 whitespace-pre-wrap text-sm leading-relaxed text-muted-foreground">
                {row.message}
              </p>
            </article>
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
