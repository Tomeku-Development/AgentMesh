import { notFound } from "next/navigation";
import { getDocById } from "@/lib/data/docs";
import { DocEditor } from "../doc-editor";

export const dynamic = "force-dynamic";

export default async function EditDocPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const doc = await getDocById(Number(id));
  if (!doc) notFound();

  return (
    <div className="mx-auto max-w-5xl">
      <header className="mb-6">
        <h1 className="font-heading text-2xl font-bold text-foreground">
          Edit document
        </h1>
        <p className="mt-1 text-sm text-muted-foreground">{doc.title}</p>
      </header>
      <DocEditor doc={doc} />
    </div>
  );
}
