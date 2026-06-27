import { NextResponse } from "next/server";
import { getHealth } from "@/lib/data/health";

export const dynamic = "force-dynamic";

export async function GET() {
  const health = await getHealth();
  const ok = health.database !== "degraded";
  return NextResponse.json(
    { ok, ...health },
    { status: ok ? 200 : 503 },
  );
}
