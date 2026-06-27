import {
  CONTENT_GROUPS,
  fieldsForGroups,
  getSiteContent,
} from "@/lib/data/site-content";
import { isDatabaseConfigured } from "@/lib/db";
import { ContentForm } from "./content-form";

export const dynamic = "force-dynamic";

export default async function AdminContentPage() {
  const values = await getSiteContent();
  const fields = fieldsForGroups(CONTENT_GROUPS);

  return (
    <div className="mx-auto max-w-3xl">
      <header className="mb-8">
        <h1 className="font-heading text-2xl font-bold text-foreground">
          Content
        </h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Edit marketing copy shown on the public site. Changes publish
          immediately.
        </p>
      </header>

      {!isDatabaseConfigured && (
        <div className="mb-6 rounded-xl border border-warning/30 bg-warning/10 p-4 text-sm text-warning">
          Database not configured. Set <code>DATABASE_URL</code> to persist
          content edits.
        </div>
      )}

      <ContentForm fields={fields} values={values} />
    </div>
  );
}
