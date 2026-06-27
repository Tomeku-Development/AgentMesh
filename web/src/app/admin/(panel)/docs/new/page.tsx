import { DocEditor } from "../doc-editor";

export const dynamic = "force-dynamic";

export default function NewDocPage() {
  return (
    <div className="mx-auto max-w-5xl">
      <header className="mb-6">
        <h1 className="font-heading text-2xl font-bold text-foreground">
          New document
        </h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Write in Markdown. Save as a draft or publish to /docs.
        </p>
      </header>
      <DocEditor />
    </div>
  );
}
