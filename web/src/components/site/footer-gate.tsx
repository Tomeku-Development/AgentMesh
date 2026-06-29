"use client";

import { usePathname } from "next/navigation";

/**
 * Hides the public footer inside areas that use their own chrome.
 */
export function FooterGate({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  if (pathname?.startsWith("/admin") || pathname?.startsWith("/presentation")) {
    return null;
  }
  return <>{children}</>;
}
