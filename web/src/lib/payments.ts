import "server-only";

export type PaymentProvider = "xendit" | "stripe" | "polar";

export type CheckoutInput = {
  provider?: PaymentProvider;
  plan: string;
  amount: number;
  currency: string;
  customerEmail?: string;
  origin: string;
};

export type CheckoutResult = {
  provider: PaymentProvider;
  providerTransactionId: string;
  checkoutUrl: string;
  rawPayload: Record<string, unknown>;
};

const PROVIDERS = ["xendit", "stripe", "polar"] as const;

export function isPaymentProvider(value: string): value is PaymentProvider {
  return PROVIDERS.includes(value as PaymentProvider);
}

export function getDefaultPaymentProvider(): PaymentProvider {
  const configured = process.env.PAYMENT_DEFAULT_PROVIDER ?? "xendit";
  return isPaymentProvider(configured) ? configured : "xendit";
}

export function getPaymentProviderStatus() {
  return [
    {
      provider: "xendit" as const,
      label: "Xendit",
      configured: Boolean(process.env.XENDIT_SECRET_KEY),
      detail: process.env.XENDIT_SECRET_KEY ? "Configured" : "Missing XENDIT_SECRET_KEY",
    },
    {
      provider: "stripe" as const,
      label: "Stripe",
      configured: Boolean(process.env.STRIPE_SECRET_KEY),
      detail: process.env.STRIPE_SECRET_KEY ? "Configured" : "Missing STRIPE_SECRET_KEY",
    },
    {
      provider: "polar" as const,
      label: "Polar",
      configured: Boolean(process.env.POLAR_ACCESS_TOKEN),
      detail: process.env.POLAR_ACCESS_TOKEN ? "Configured" : "Missing POLAR_ACCESS_TOKEN",
    },
  ];
}

export function getPlanPrice(plan: string) {
  const normalized = plan.toLowerCase();
  if (normalized === "pro") {
    return {
      plan: "pro",
      amount: Number(process.env.PAYMENT_PRO_AMOUNT ?? 9900),
      currency: process.env.PAYMENT_PRO_CURRENCY ?? "USD",
    };
  }
  return null;
}

function successUrl(origin: string, provider: PaymentProvider) {
  return `${origin}/pricing?checkout=success&provider=${provider}`;
}

function failureUrl(origin: string, provider: PaymentProvider) {
  return `${origin}/pricing?checkout=failed&provider=${provider}`;
}

function amountForProvider(amount: number, provider: PaymentProvider) {
  if (provider === "xendit") return Math.round(amount / 100);
  return amount;
}

async function createXenditCheckout(input: CheckoutInput): Promise<CheckoutResult> {
  const secret = process.env.XENDIT_SECRET_KEY;
  if (!secret) throw new Error("Xendit is not configured.");

  const provider = "xendit";
  const externalId = `agentmesh-${input.plan}-${crypto.randomUUID()}`;
  const body = {
    external_id: externalId,
    amount: amountForProvider(input.amount, provider),
    currency: input.currency,
    payer_email: input.customerEmail,
    description: `AgentMesh ${input.plan} plan`,
    success_redirect_url: successUrl(input.origin, provider),
    failure_redirect_url: failureUrl(input.origin, provider),
  };

  const res = await fetch("https://api.xendit.co/v2/invoices", {
    method: "POST",
    headers: {
      Authorization: `Basic ${Buffer.from(`${secret}:`).toString("base64")}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(body),
  });
  const data = (await res.json().catch(() => ({}))) as Record<string, unknown>;
  if (!res.ok) throw new Error(String(data.message ?? "Xendit checkout failed."));

  return {
    provider,
    providerTransactionId: String(data.id ?? externalId),
    checkoutUrl: String(data.invoice_url ?? ""),
    rawPayload: data,
  };
}

async function createStripeCheckout(input: CheckoutInput): Promise<CheckoutResult> {
  const secret = process.env.STRIPE_SECRET_KEY;
  if (!secret) throw new Error("Stripe is not configured.");

  const provider = "stripe";
  const priceId = process.env.STRIPE_PRO_PRICE_ID;
  const params = new URLSearchParams({
    mode: priceId ? "subscription" : "payment",
    success_url: successUrl(input.origin, provider),
    cancel_url: failureUrl(input.origin, provider),
    "metadata[plan]": input.plan,
  });
  if (input.customerEmail) params.set("customer_email", input.customerEmail);
  if (priceId) {
    params.set("line_items[0][price]", priceId);
    params.set("line_items[0][quantity]", "1");
  } else {
    params.set("line_items[0][price_data][currency]", input.currency.toLowerCase());
    params.set("line_items[0][price_data][unit_amount]", String(input.amount));
    params.set("line_items[0][price_data][product_data][name]", `AgentMesh ${input.plan}`);
    params.set("line_items[0][quantity]", "1");
  }

  const res = await fetch("https://api.stripe.com/v1/checkout/sessions", {
    method: "POST",
    headers: {
      Authorization: `Bearer ${secret}`,
      "Content-Type": "application/x-www-form-urlencoded",
    },
    body: params,
  });
  const data = (await res.json().catch(() => ({}))) as Record<string, unknown>;
  if (!res.ok) {
    const error = data.error as { message?: string } | undefined;
    throw new Error(error?.message ?? "Stripe checkout failed.");
  }

  return {
    provider,
    providerTransactionId: String(data.id ?? crypto.randomUUID()),
    checkoutUrl: String(data.url ?? ""),
    rawPayload: data,
  };
}

async function createPolarCheckout(input: CheckoutInput): Promise<CheckoutResult> {
  const token = process.env.POLAR_ACCESS_TOKEN;
  const productId = process.env.POLAR_PRO_PRODUCT_ID;
  if (!token || !productId) throw new Error("Polar is not configured.");

  const provider = "polar";
  const res = await fetch("https://api.polar.sh/v1/checkouts/", {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      products: [productId],
      customer_email: input.customerEmail,
      success_url: successUrl(input.origin, provider),
      metadata: { plan: input.plan },
    }),
  });
  const data = (await res.json().catch(() => ({}))) as Record<string, unknown>;
  if (!res.ok) throw new Error(String(data.detail ?? "Polar checkout failed."));

  return {
    provider,
    providerTransactionId: String(data.id ?? crypto.randomUUID()),
    checkoutUrl: String(data.url ?? data.checkout_url ?? ""),
    rawPayload: data,
  };
}

export async function createCheckout(input: CheckoutInput): Promise<CheckoutResult> {
  const provider = input.provider ?? getDefaultPaymentProvider();
  const checkout =
    provider === "xendit"
      ? await createXenditCheckout(input)
      : provider === "stripe"
        ? await createStripeCheckout(input)
        : await createPolarCheckout(input);
  if (!checkout.checkoutUrl) {
    throw new Error(`${provider} did not return a checkout URL.`);
  }
  return checkout;
}
