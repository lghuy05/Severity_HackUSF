import "./globals.css";
import type { Metadata } from "next";
import { ReactNode } from "react";
import { Manrope, Newsreader } from "next/font/google";

import { AppMenu } from "@/components/AppMenu";

const manrope = Manrope({ subsets: ["latin"], variable: "--font-sans" });
const newsreader = Newsreader({ subsets: ["latin"], variable: "--font-display" });

export const metadata: Metadata = {
  title: "Health Equity Bridge",
  description: "Clear guidance from symptoms to next steps",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body className={`${manrope.variable} ${newsreader.variable}`}>
        <AppMenu />
        {children}
      </body>
    </html>
  );
}
