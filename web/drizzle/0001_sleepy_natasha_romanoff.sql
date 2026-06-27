CREATE TABLE "media_assets" (
	"id" serial PRIMARY KEY NOT NULL,
	"key" varchar(512) NOT NULL,
	"url" text NOT NULL,
	"filename" varchar(256) NOT NULL,
	"content_type" varchar(128) NOT NULL,
	"size" integer DEFAULT 0 NOT NULL,
	"alt" varchar(300),
	"created_at" timestamp with time zone DEFAULT now() NOT NULL
);
--> statement-breakpoint
CREATE TABLE "site_content" (
	"id" serial PRIMARY KEY NOT NULL,
	"key" varchar(120) NOT NULL,
	"value" text DEFAULT '' NOT NULL,
	"updated_at" timestamp with time zone DEFAULT now() NOT NULL
);
--> statement-breakpoint
CREATE UNIQUE INDEX "site_content_key_idx" ON "site_content" USING btree ("key");