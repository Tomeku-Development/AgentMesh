"use client";

import { usePathname } from "next/navigation";

/**
 * Hides the public footer inside the admin area, which uses its own chrome.
 */
export function FooterGate({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  if (pathname?.startsWith("/admin")) return null;
  return <>{children}</>;
}
