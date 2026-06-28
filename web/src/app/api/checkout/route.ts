import { NextRequest, NextResponse } from "next/server";
import { db } from "@/lib/db";
import { paymentTransactions } from "@/lib/db/schema";
import {
  createCheckout,
  getDefaultPaymentProvider,
  getPlanPrice,
  isPaymentProvider,
} from "@/lib/payments";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

function originFromRequest(req: NextRequest) {
  const configured = process.env.NEXT_PUBLIC_SITE_URL || process.env.BETTER_AUTH_URL;
  if (configured) return new URL(configured).origin;
  return req.nextUrl.origin;
}

export async function POST(req: NextRequest) {
  const formData = await req.formData();
  const planRaw = String(formData.get("plan") ?? "pro");
  const providerRaw = String(formData.get("provider") ?? "");
  const customerEmail = String(formData.get("email") ?? "").trim().toLowerCase();
  const plan = getPlanPrice(planRaw);

  if (!plan) {
    return NextResponse.redirect(new URL("/pricing?checkout=invalid-plan", req.url));
  }

  const provider = providerRaw && isPaymentProvider(providerRaw)
    ? providerRaw
    : getDefaultPaymentProvider();

  try {
    const checkout = await createCheckout({
      provider,
      plan: plan.plan,
      amount: plan.amount,
      currency: plan.currency,
      customerEmail: customerEmail || undefined,
      origin: originFromRequest(req),
    });

    if (db) {
      await db.insert(paymentTransactions).values({
        provider: checkout.provider,
        providerTransactionId: checkout.providerTransactionId,
        checkoutUrl: checkout.checkoutUrl,
        plan: plan.plan,
        amount: plan.amount,
        currency: plan.currency,
        status: "checkout_created",
        customerEmail: customerEmail || null,
        rawPayload: checkout.rawPayload,
        metadata: { source: "pricing" },
      });
    }

    return NextResponse.redirect(checkout.checkoutUrl, 303);
  } catch (error) {
    console.error("[checkout] create failed:", error);
    const url = new URL("/contact", req.url);
    url.searchParams.set("intent", "checkout");
    url.searchParams.set("plan", plan.plan);
    url.searchParams.set("provider", provider);
    url.searchParams.set("checkout", "setup-required");
    return NextResponse.redirect(url, 303);
  }
}
