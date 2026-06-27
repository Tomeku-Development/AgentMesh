import { NextResponse } from "next/server";
import { getNetworkStats } from "@/lib/data/stats";

export const dynamic = "force-dynamic";

export async function GET() {
  const stats = await getNetworkStats();
  return NextResponse.json(stats);
}
