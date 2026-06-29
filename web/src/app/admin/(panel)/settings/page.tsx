import {
  SETTINGS_GROUPS,
  fieldsForGroups,
  getSiteContent,
} from "@/lib/data/site-content";
import { isDatabaseConfigured } from "@/lib/db";
import { ContentForm } from "../content/content-form";

export const dynamic = "force-dynamic";

export default async function AdminSettingsPage() {
  const values = await getSiteContent();
  const fields = fieldsForGroups(SETTINGS_GROUPS);

  return (
    <div className="mx-auto max-w-3xl">
      <header className="mb-8">
        <h1 className="font-heading text-2xl font-bold text-foreground">
          Website Settings
        </h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Global site identity, default SEO metadata, and presentation mode
          settings. Applied across the public site.
        </p>
      </header>

      {!isDatabaseConfigured && (
        <div className="mb-6 rounded-xl border border-warning/30 bg-warning/10 p-4 text-sm text-warning">
          Database not configured. Set <code>DATABASE_URL</code> to persist
          settings.
        </div>
      )}

      <ContentForm fields={fields} values={values} />
    </div>
  );
}
