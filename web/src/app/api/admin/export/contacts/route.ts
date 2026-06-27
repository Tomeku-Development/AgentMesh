import { getContactSubmissions } from "@/lib/data/admin";
import { toCsv, csvFilename } from "@/lib/csv";

export const dynamic = "force-dynamic";

export async function GET() {
  const rows = await getContactSubmissions();
  const csv = toCsv(
    ["id", "name", "email", "company", "message", "created_at"],
    rows.map((r) => [
      r.id,
      r.name,
      r.email,
      r.company ?? "",
      r.message,
      new Date(r.createdAt).toISOString(),
    ]),
  );

  return new Response(csv, {
    headers: {
      "Content-Type": "text/csv; charset=utf-8",
      "Content-Disposition": `attachment; filename="${csvFilename("contacts")}"`,
      "Cache-Control": "no-store",
    },
  });
}
