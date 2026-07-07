import type { Metadata } from "next";

import { NavBar } from "@/components/NavBar";
import { Providers } from "./providers";
import "./globals.css";

export const metadata: Metadata = {
  title: "BeerIQ — Brewery Intelligence",
  description: "Live tap lists, events, food trucks, and brewery scores across America.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link
          href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,600;9..144,700&family=Inter:wght@400;500;600;700&display=swap"
          rel="stylesheet"
        />
      </head>
      <body>
        <Providers>
          <NavBar />
          {children}
          <footer className="mt-16 border-t border-border py-8 text-center text-xs text-muted-foreground">
            Directory data via Open Brewery DB · BeerIQ © 2026
          </footer>
        </Providers>
      </body>
    </html>
  );
}
