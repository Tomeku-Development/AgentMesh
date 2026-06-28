import { NextResponse } from "next/server";
import { getAllPaymentTransactions } from "@/lib/data/admin";
import { getAdminSession } from "@/lib/session";

export const dynamic = "force-dynamic";

function csvCell(value: unknown) {
  const text = value == null ? "" : String(value);
  return `"${text.replace(/"/g, '""')}"`;
}

export async function GET() {
  const session = await getAdminSession();
  if (!session) {
    return NextResponse.json({ error: "Forbidden" }, { status: 403 });
  }

  const rows = await getAllPaymentTransactions();
  const header = [
    "id",
    "provider",
    "providerTransactionId",
    "plan",
    "amount",
    "currency",
    "status",
    "customerEmail",
    "checkoutUrl",
    "createdAt",
    "updatedAt",
  ];

  const csv = [
    header.join(","),
    ...rows.map((row) =>
      [
        row.id,
        row.provider,
        row.providerTransactionId,
        row.plan,
        row.amount,
        row.currency,
        row.status,
        row.customerEmail,
        row.checkoutUrl,
        row.createdAt,
        row.updatedAt,
      ]
        .map(csvCell)
        .join(","),
    ),
  ].join("\n");

  return new NextResponse(csv, {
    headers: {
      "Content-Type": "text/csv; charset=utf-8",
      "Content-Disposition": `attachment; filename="agentmesh-payments-${new Date()
        .toISOString()
        .slice(0, 10)}.csv"`,
    },
  });
}
