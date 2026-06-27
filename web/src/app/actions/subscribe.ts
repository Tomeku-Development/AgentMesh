"use server";

import { db } from "@/lib/db";
import { subscribers } from "@/lib/db/schema";

export type SubscribeState = {
  status: "idle" | "success" | "error";
  message: string;
};

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

export async function subscribe(
  _prev: SubscribeState,
  formData: FormData,
): Promise<SubscribeState> {
  const email = String(formData.get("email") ?? "")
    .trim()
    .toLowerCase();

  if (!EMAIL_RE.test(email) || email.length > 320) {
    return { status: "error", message: "Please enter a valid email address." };
  }

  if (!db) {
    // No database configured — accept gracefully so the UX still works.
    return {
      status: "success",
      message: "Thanks! You're on the list.",
    };
  }

  try {
    await db
      .insert(subscribers)
      .values({ email })
      .onConflictDoNothing({ target: subscribers.email });

    return { status: "success", message: "Thanks! You're on the list." };
  } catch (error) {
    console.error("[subscribe] failed:", error);
    return {
      status: "error",
      message: "Something went wrong. Please try again.",
    };
  }
}
