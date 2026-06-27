import { getSubscribers } from "@/lib/data/admin";
import { toCsv, csvFilename } from "@/lib/csv";

export const dynamic = "force-dynamic";

export async function GET() {
  const rows = await getSubscribers();
  const csv = toCsv(
    ["id", "email", "created_at"],
    rows.map((r) => [r.id, r.email, new Date(r.createdAt).toISOString()]),
  );

  return new Response(csv, {
    headers: {
      "Content-Type": "text/csv; charset=utf-8",
      "Content-Disposition": `attachment; filename="${csvFilename("subscribers")}"`,
      "Cache-Control": "no-store",
    },
  });
}
