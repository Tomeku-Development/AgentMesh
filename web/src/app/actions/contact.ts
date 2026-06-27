"use server";

import { db } from "@/lib/db";
import { contactSubmissions } from "@/lib/db/schema";

export type ContactState = {
  status: "idle" | "success" | "error";
  message: string;
  errors?: Partial<Record<"name" | "email" | "message", string>>;
};

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

export async function submitContact(
  _prev: ContactState,
  formData: FormData,
): Promise<ContactState> {
  const name = String(formData.get("name") ?? "").trim();
  const email = String(formData.get("email") ?? "")
    .trim()
    .toLowerCase();
  const company = String(formData.get("company") ?? "").trim();
  const message = String(formData.get("message") ?? "").trim();

  const errors: ContactState["errors"] = {};
  if (name.length < 2 || name.length > 200) errors.name = "Enter your name.";
  if (!EMAIL_RE.test(email) || email.length > 320)
    errors.email = "Enter a valid email.";
  if (message.length < 10 || message.length > 5000)
    errors.message = "Tell us a little more (10+ characters).";

  if (Object.keys(errors).length > 0) {
    return { status: "error", message: "Please fix the fields below.", errors };
  }

  if (!db) {
    // No DB configured — accept gracefully so the flow still works.
    return {
      status: "success",
      message: "Thanks for reaching out. We'll be in touch soon.",
    };
  }

  try {
    await db.insert(contactSubmissions).values({
      name,
      email,
      company: company || null,
      message,
    });
    return {
      status: "success",
      message: "Thanks for reaching out. We'll be in touch soon.",
    };
  } catch (error) {
    console.error("[contact] failed:", error);
    return {
      status: "error",
      message: "Something went wrong. Please try again.",
    };
  }
}
