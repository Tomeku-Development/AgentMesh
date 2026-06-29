import "server-only";
import { db } from "@/lib/db";
import { siteContent } from "@/lib/db/schema";

/**
 * Editable marketing copy. Each field has a stable key, a label for the admin
 * UI, and a default used when the database has no override (or no DB at all).
 */
export type ContentField = {
  key: string;
  label: string;
  group: string;
  multiline?: boolean;
  default: string;
};

export const CONTENT_FIELDS: ContentField[] = [
  {
    key: "hero.eyebrow",
    label: "Hero eyebrow",
    group: "Hero",
    default: "The Operating System",
  },
  {
    key: "hero.title_line1",
    label: "Hero title — line 1",
    group: "Hero",
    default: "For Autonomous",
  },
  {
    key: "hero.title_line2",
    label: "Hero title — line 2",
    group: "Hero",
    default: "Organizations",
  },
  {
    key: "hero.description",
    label: "Hero description",
    group: "Hero",
    multiline: true,
    default:
      "AgentMesh is a decentralized multi-agent platform where AI agents collaborate, reason, and execute trusted on-chain actions on Casper.",
  },
  {
    key: "cta.title",
    label: "CTA title",
    group: "Call to action",
    multiline: true,
    default: "Deploy Your First\nAutonomous Organization",
  },
  {
    key: "cta.description",
    label: "CTA description",
    group: "Call to action",
    multiline: true,
    default:
      "Join the builders shaping the agent economy on Casper. Get early access to the AgentMesh platform and start coordinating intelligent, on-chain agents today.",
  },
  {
    key: "settings.site_name",
    label: "Site name",
    group: "Site & SEO",
    default: "AgentMesh",
  },
  {
    key: "settings.seo_title",
    label: "Default SEO title",
    group: "Site & SEO",
    default: "AgentMesh — The Operating System for Autonomous Organizations",
  },
  {
    key: "settings.seo_description",
    label: "Default meta description",
    group: "Site & SEO",
    multiline: true,
    default:
      "AgentMesh is a decentralized multi-agent platform where AI agents collaborate, reason, and execute trusted on-chain actions on Casper.",
  },
  {
    key: "settings.og_image",
    label: "Default social image URL (OG image)",
    group: "Site & SEO",
    default: "",
  },
  {
    key: "settings.contact_email",
    label: "Public contact email",
    group: "Site & SEO",
    default: "hello@agentmesh.example",
  },
  {
    key: "settings.twitter",
    label: "X / Twitter handle",
    group: "Site & SEO",
    default: "OfficialTomeku",
  },
  {
    key: "presentation.youtube",
    label: "YouTube video ID or URL",
    group: "Presentation",
    default: "",
  },
  {
    key: "presentation.mode_label",
    label: "Mode label",
    group: "Presentation",
    default: "Presentation mode",
  },
  {
    key: "presentation.launch_title",
    label: "Launch title",
    group: "Presentation",
    default: "Launch Presentation",
  },
  {
    key: "presentation.launch_description",
    label: "Launch description",
    group: "Presentation",
    multiline: true,
    default:
      "One click opens fullscreen and starts the video. Browser security requires this launch click before fullscreen can begin.",
  },
  {
    key: "presentation.helper_text",
    label: "Playback helper text",
    group: "Presentation",
    default: "YouTube controls remain available during playback.",
  },
  {
    key: "presentation.countdown_title",
    label: "Countdown title",
    group: "Presentation",
    default: "Entering AgentMesh",
  },
  {
    key: "presentation.countdown_description",
    label: "Countdown description",
    group: "Presentation",
    multiline: true,
    default: "The main website opens automatically when the countdown finishes.",
  },
  {
    key: "presentation.countdown_seconds",
    label: "Countdown seconds",
    group: "Presentation",
    default: "5",
  },
  {
    key: "presentation.redirect_path",
    label: "Redirect path after countdown",
    group: "Presentation",
    default: "/",
  },
];

/** Field groups that make up the editable "content" (vs. global settings). */
export const CONTENT_GROUPS = ["Hero", "Call to action"];
export const SETTINGS_GROUPS = ["Site & SEO", "Presentation"];

export function fieldsForGroups(groups: string[]): ContentField[] {
  return CONTENT_FIELDS.filter((f) => groups.includes(f.group));
}

export type SiteContentMap = Record<string, string>;

export function defaultContent(): SiteContentMap {
  return Object.fromEntries(CONTENT_FIELDS.map((f) => [f.key, f.default]));
}

export async function getSiteContent(): Promise<SiteContentMap> {
  const content = defaultContent();
  if (!db) return content;

  try {
    const rows = await db.select().from(siteContent);
    for (const row of rows) {
      // Only surface known keys; ignore stale ones.
      if (row.key in content && row.value.trim().length > 0) {
        content[row.key] = row.value;
      }
    }
  } catch (error) {
    console.error("[site-content] load failed:", error);
  }
  return content;
}
