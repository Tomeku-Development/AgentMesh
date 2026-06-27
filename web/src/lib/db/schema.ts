import {
  pgTable,
  serial,
  text,
  varchar,
  timestamp,
  integer,
  bigint,
  boolean,
  uniqueIndex,
} from "drizzle-orm/pg-core";

/**
 * Live network metrics shown in the stats bar on the landing page.
 * A single authoritative row is kept and updated over time.
 */
export const networkStats = pgTable("network_stats", {
  id: serial("id").primaryKey(),
  agentsOnline: integer("agents_online").notNull().default(0),
  transactions: integer("transactions").notNull().default(0),
  proposals: integer("proposals").notNull().default(0),
  // TVL stored in whole CSPR units
  tvlCspr: bigint("tvl_cspr", { mode: "number" }).notNull().default(0),
  updatedAt: timestamp("updated_at", { withTimezone: true })
    .notNull()
    .defaultNow(),
});

/**
 * Newsletter / early-access signups captured from the site.
 */
export const subscribers = pgTable(
  "subscribers",
  {
    id: serial("id").primaryKey(),
    email: varchar("email", { length: 320 }).notNull(),
    createdAt: timestamp("created_at", { withTimezone: true })
      .notNull()
      .defaultNow(),
  },
  (table) => ({
    emailIdx: uniqueIndex("subscribers_email_idx").on(table.email),
  }),
);

/**
 * Contact / "talk to us" form submissions.
 */
export const contactSubmissions = pgTable("contact_submissions", {
  id: serial("id").primaryKey(),
  name: varchar("name", { length: 200 }).notNull(),
  email: varchar("email", { length: 320 }).notNull(),
  company: varchar("company", { length: 200 }),
  message: text("message").notNull(),
  createdAt: timestamp("created_at", { withTimezone: true })
    .notNull()
    .defaultNow(),
});

/**
 * Editable site content — a key/value store for marketing copy that admins
 * can change without a deploy (e.g. hero title, CTA text).
 */
export const siteContent = pgTable(
  "site_content",
  {
    id: serial("id").primaryKey(),
    key: varchar("key", { length: 120 }).notNull(),
    value: text("value").notNull().default(""),
    updatedAt: timestamp("updated_at", { withTimezone: true })
      .notNull()
      .defaultNow(),
  },
  (table) => ({
    keyIdx: uniqueIndex("site_content_key_idx").on(table.key),
  }),
);

/**
 * Images and files uploaded to S3-compatible storage (Cloudflare R2 / AWS S3).
 * The object lives in the bucket; this row tracks metadata + public URL.
 */
export const mediaAssets = pgTable("media_assets", {
  id: serial("id").primaryKey(),
  key: varchar("key", { length: 512 }).notNull(),
  url: text("url").notNull(),
  filename: varchar("filename", { length: 256 }).notNull(),
  contentType: varchar("content_type", { length: 128 }).notNull(),
  size: integer("size").notNull().default(0),
  alt: varchar("alt", { length: 300 }),
  createdAt: timestamp("created_at", { withTimezone: true })
    .notNull()
    .defaultNow(),
});

export type NetworkStats = typeof networkStats.$inferSelect;
export type NewSubscriber = typeof subscribers.$inferInsert;
export type NewContactSubmission = typeof contactSubmissions.$inferInsert;
export type SiteContentRow = typeof siteContent.$inferSelect;
export type MediaAsset = typeof mediaAssets.$inferSelect;

/**
 * Documentation pages managed via the admin (a lightweight docs CMS).
 */
export const docPages = pgTable(
  "doc_pages",
  {
    id: serial("id").primaryKey(),
    slug: varchar("slug", { length: 160 }).notNull(),
    title: varchar("title", { length: 240 }).notNull(),
    category: varchar("category", { length: 120 }).notNull().default("General"),
    summary: text("summary").notNull().default(""),
    body: text("body").notNull().default(""),
    sortOrder: integer("sort_order").notNull().default(0),
    published: boolean("published").notNull().default(false),
    seoTitle: varchar("seo_title", { length: 240 }),
    seoDescription: varchar("seo_description", { length: 320 }),
    createdAt: timestamp("created_at", { withTimezone: true })
      .notNull()
      .defaultNow(),
    updatedAt: timestamp("updated_at", { withTimezone: true })
      .notNull()
      .defaultNow(),
  },
  (table) => ({
    slugIdx: uniqueIndex("doc_pages_slug_idx").on(table.slug),
  }),
);

export type DocPage = typeof docPages.$inferSelect;
export type NewDocPage = typeof docPages.$inferInsert;
