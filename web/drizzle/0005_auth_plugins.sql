ALTER TABLE "user" ADD COLUMN IF NOT EXISTS "last_login_method" text;
ALTER TABLE "session" ADD COLUMN IF NOT EXISTS "active_organization_id" text;
ALTER TABLE "session" ADD COLUMN IF NOT EXISTS "active_team_id" text;

CREATE TABLE IF NOT EXISTS "passkey" (
  "id" text PRIMARY KEY NOT NULL,
  "name" text,
  "public_key" text NOT NULL,
  "user_id" text NOT NULL,
  "credential_id" text NOT NULL,
  "counter" integer NOT NULL,
  "device_type" text NOT NULL,
  "backed_up" boolean NOT NULL,
  "transports" text,
  "created_at" timestamp DEFAULT now() NOT NULL,
  "aaguid" text,
  CONSTRAINT "passkey_user_id_user_id_fk"
    FOREIGN KEY ("user_id") REFERENCES "user"("id") ON DELETE cascade
);

CREATE INDEX IF NOT EXISTS "passkey_user_id_idx" ON "passkey" ("user_id");
CREATE INDEX IF NOT EXISTS "passkey_credential_id_idx" ON "passkey" ("credential_id");

CREATE TABLE IF NOT EXISTS "apikey" (
  "id" text PRIMARY KEY NOT NULL,
  "config_id" text DEFAULT 'default' NOT NULL,
  "name" text,
  "start" text,
  "prefix" text,
  "key" text NOT NULL,
  "reference_id" text NOT NULL,
  "refill_interval" integer,
  "refill_amount" integer,
  "last_refill_at" timestamp,
  "enabled" boolean DEFAULT true,
  "rate_limit_enabled" boolean DEFAULT true,
  "rate_limit_time_window" integer DEFAULT 86400000,
  "rate_limit_max" integer DEFAULT 10,
  "request_count" integer DEFAULT 0,
  "remaining" integer,
  "last_request" timestamp,
  "expires_at" timestamp,
  "created_at" timestamp DEFAULT now() NOT NULL,
  "updated_at" timestamp DEFAULT now() NOT NULL,
  "permissions" text,
  "metadata" text
);

CREATE INDEX IF NOT EXISTS "apikey_config_id_idx" ON "apikey" ("config_id");
CREATE INDEX IF NOT EXISTS "apikey_reference_id_idx" ON "apikey" ("reference_id");
CREATE INDEX IF NOT EXISTS "apikey_key_idx" ON "apikey" ("key");

CREATE TABLE IF NOT EXISTS "organization" (
  "id" text PRIMARY KEY NOT NULL,
  "name" text NOT NULL,
  "slug" text NOT NULL,
  "logo" text,
  "metadata" text,
  "created_at" timestamp DEFAULT now() NOT NULL,
  "updated_at" timestamp,
  CONSTRAINT "organization_slug_unique" UNIQUE ("slug")
);

CREATE TABLE IF NOT EXISTS "member" (
  "id" text PRIMARY KEY NOT NULL,
  "organization_id" text NOT NULL,
  "user_id" text NOT NULL,
  "role" text DEFAULT 'member' NOT NULL,
  "created_at" timestamp DEFAULT now() NOT NULL,
  CONSTRAINT "member_organization_id_organization_id_fk"
    FOREIGN KEY ("organization_id") REFERENCES "organization"("id") ON DELETE cascade,
  CONSTRAINT "member_user_id_user_id_fk"
    FOREIGN KEY ("user_id") REFERENCES "user"("id") ON DELETE cascade
);

CREATE TABLE IF NOT EXISTS "invitation" (
  "id" text PRIMARY KEY NOT NULL,
  "organization_id" text NOT NULL,
  "email" text NOT NULL,
  "role" text NOT NULL,
  "status" text DEFAULT 'pending' NOT NULL,
  "expires_at" timestamp,
  "inviter_id" text NOT NULL,
  "team_id" text,
  "created_at" timestamp DEFAULT now() NOT NULL,
  CONSTRAINT "invitation_organization_id_organization_id_fk"
    FOREIGN KEY ("organization_id") REFERENCES "organization"("id") ON DELETE cascade,
  CONSTRAINT "invitation_inviter_id_user_id_fk"
    FOREIGN KEY ("inviter_id") REFERENCES "user"("id") ON DELETE cascade
);

CREATE TABLE IF NOT EXISTS "team" (
  "id" text PRIMARY KEY NOT NULL,
  "name" text NOT NULL,
  "organization_id" text NOT NULL,
  "created_at" timestamp DEFAULT now() NOT NULL,
  "updated_at" timestamp,
  CONSTRAINT "team_organization_id_organization_id_fk"
    FOREIGN KEY ("organization_id") REFERENCES "organization"("id") ON DELETE cascade
);

CREATE TABLE IF NOT EXISTS "team_member" (
  "id" text PRIMARY KEY NOT NULL,
  "team_id" text NOT NULL,
  "user_id" text NOT NULL,
  "created_at" timestamp DEFAULT now(),
  CONSTRAINT "team_member_team_id_team_id_fk"
    FOREIGN KEY ("team_id") REFERENCES "team"("id") ON DELETE cascade,
  CONSTRAINT "team_member_user_id_user_id_fk"
    FOREIGN KEY ("user_id") REFERENCES "user"("id") ON DELETE cascade
);
