import type { Metadata } from "next";
import { GeistMono } from "geist/font/mono";
import { GeistSans } from "geist/font/sans";
import { Providers } from "@/app/providers";
import "./globals.css";

export const metadata: Metadata = {
  title: {
    default: "ResolveAI",
    template: "%s · ResolveAI",
  },
  description:
    "Enterprise AI support with grounded citations, human approvals, and observable agent operations.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${GeistSans.variable} ${GeistMono.variable} h-full antialiased`}
    >
      <body className="min-h-full font-sans text-on-surface">
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
