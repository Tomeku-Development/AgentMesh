import type { Metadata } from "next";
import { Sora, Inter, JetBrains_Mono } from "next/font/google";
import "./globals.css";
import { Navbar } from "@/components/site/navbar";
import { Footer } from "@/components/site/footer";
import { FooterGate } from "@/components/site/footer-gate";
import { getSiteContent } from "@/lib/data/site-content";

const inter = Inter({
  variable: "--font-sans",
  subsets: ["latin"],
  display: "swap",
});

const sora = Sora({
  variable: "--font-heading",
  subsets: ["latin"],
  weight: ["400", "600", "700", "800"],
  display: "swap",
});

const jetbrainsMono = JetBrains_Mono({
  variable: "--font-mono",
  subsets: ["latin"],
  display: "swap",
});

export async function generateMetadata(): Promise<Metadata> {
  const c = await getSiteContent();
  const title = c["settings.seo_title"];
  const description = c["settings.seo_description"];
  const ogImage = c["settings.og_image"];
  const twitter = c["settings.twitter"];

  return {
    title,
    description,
    metadataBase: new URL("https://agentmesh.world"),
    openGraph: {
      title,
      description,
      type: "website",
      ...(ogImage ? { images: [{ url: ogImage }] } : {}),
    },
    twitter: {
      card: ogImage ? "summary_large_image" : "summary",
      title,
      description,
      ...(twitter ? { creator: `@${twitter.replace(/^@/, "")}` } : {}),
      ...(ogImage ? { images: [ogImage] } : {}),
    },
  };
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${inter.variable} ${sora.variable} ${jetbrainsMono.variable} h-full`}
    >
      <body className="min-h-full flex flex-col bg-background text-foreground">
        <Navbar />
        <div className="flex flex-1 flex-col">{children}</div>
        <FooterGate>
          <Footer />
        </FooterGate>
      </body>
    </html>
  );
}
