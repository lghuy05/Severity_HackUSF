import "./globals.css";
import type { Metadata } from "next";
import { ReactNode } from "react";
import { Inter } from "next/font/google";

import { AppMenu } from "@/components/AppMenu";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Severity AI",
  description: "Guided AI healthcare navigation experience",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <AppMenu />
        {children}
      </body>
    </html>
  );
}
