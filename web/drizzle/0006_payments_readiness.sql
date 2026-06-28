CREATE TABLE IF NOT EXISTS "payment_transactions" (
  "id" serial PRIMARY KEY NOT NULL,
  "provider" varchar(32) NOT NULL,
  "provider_transaction_id" varchar(256),
  "checkout_url" text,
  "plan" varchar(80) NOT NULL,
  "amount" integer NOT NULL,
  "currency" varchar(12) DEFAULT 'USD' NOT NULL,
  "status" varchar(40) DEFAULT 'pending' NOT NULL,
  "customer_email" varchar(320),
  "metadata" jsonb DEFAULT '{}'::jsonb,
  "raw_payload" jsonb,
  "created_at" timestamp with time zone DEFAULT now() NOT NULL,
  "updated_at" timestamp with time zone DEFAULT now() NOT NULL
);

CREATE UNIQUE INDEX IF NOT EXISTS "payment_transactions_provider_id_idx"
  ON "payment_transactions" ("provider", "provider_transaction_id");
