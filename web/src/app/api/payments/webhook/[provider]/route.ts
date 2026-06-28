import { NextRequest, NextResponse } from "next/server";
import { createHmac, timingSafeEqual } from "node:crypto";
import { and, eq } from "drizzle-orm";
import { db } from "@/lib/db";
import { paymentTransactions } from "@/lib/db/schema";
import { isPaymentProvider } from "@/lib/payments";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

type Params = {
  params: Promise<{ provider: string }>;
};

function getProviderId(provider: string, payload: Record<string, unknown>) {
  if (provider === "xendit") {
    return String(payload.id ?? payload.external_id ?? "");
  }
  if (provider === "stripe") {
    const data = payload.data as { object?: { id?: string } } | undefined;
    return String(data?.object?.id ?? payload.id ?? "");
  }
  return String(payload.id ?? payload.checkout_id ?? "");
}

function getStatus(provider: string, payload: Record<string, unknown>) {
  if (provider === "stripe") return String(payload.type ?? "webhook_received");
  return String(payload.status ?? payload.type ?? "webhook_received").toLowerCase();
}

function verifyStripeSignature(rawBody: string, signature: string, secret: string) {
  const parts = Object.fromEntries(
    signature.split(",").map((part) => {
      const [key, value] = part.split("=");
      return [key, value];
    }),
  );
  const timestamp = parts.t;
  const signed = parts.v1;
  if (!timestamp || !signed) return false;
  const expected = createHmac("sha256", secret)
    .update(`${timestamp}.${rawBody}`)
    .digest("hex");
  const left = Buffer.from(expected);
  const right = Buffer.from(signed);
  return left.length === right.length && timingSafeEqual(left, right);
}

function verifyWebhook(req: NextRequest, provider: string, rawBody: string) {
  if (provider === "xendit" && process.env.XENDIT_WEBHOOK_TOKEN) {
    return req.headers.get("x-callback-token") === process.env.XENDIT_WEBHOOK_TOKEN;
  }
  if (provider === "stripe" && process.env.STRIPE_WEBHOOK_SECRET) {
    const signature = req.headers.get("stripe-signature");
    return signature
      ? verifyStripeSignature(rawBody, signature, process.env.STRIPE_WEBHOOK_SECRET)
      : false;
  }
  return true;
}

export async function POST(req: NextRequest, { params }: Params) {
  const { provider } = await params;
  if (!isPaymentProvider(provider)) {
    return NextResponse.json({ ok: false, error: "Invalid provider" }, { status: 400 });
  }

  const rawBody = await req.text();
  if (!verifyWebhook(req, provider, rawBody)) {
    return NextResponse.json({ ok: false, error: "Invalid signature" }, { status: 401 });
  }

  let payload: Record<string, unknown>;
  try {
    payload = JSON.parse(rawBody || "{}") as Record<string, unknown>;
  } catch {
    return NextResponse.json({ ok: false, error: "Invalid JSON" }, { status: 400 });
  }
  const providerTransactionId = getProviderId(provider, payload);
  const status = getStatus(provider, payload);

  if (!db || !providerTransactionId) {
    return NextResponse.json({ ok: true });
  }

  try {
    await db
      .update(paymentTransactions)
      .set({
        status,
        rawPayload: payload,
        updatedAt: new Date(),
      })
      .where(
        and(
          eq(paymentTransactions.provider, provider),
          eq(paymentTransactions.providerTransactionId, providerTransactionId),
        ),
      );
  } catch (error) {
    console.error("[payments] webhook persistence failed:", error);
  }

  return NextResponse.json({ ok: true });
}
