import type { Metadata } from "next";

import { NavBar } from "@/components/NavBar";
import { Providers } from "./providers";
import "./globals.css";

export const metadata: Metadata = {
  title: "BrewIQ",
  description: "Discover breweries, live tap lists, and BrewIQ scores.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        <Providers>
          <NavBar />
          {children}
        </Providers>
      </body>
    </html>
  );
}
