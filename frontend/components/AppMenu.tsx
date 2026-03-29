"use client";

import Image from "next/image";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { BookText, CalendarHeart, ClipboardPlus, Home, UserRound, Workflow } from "lucide-react";
import { getAppCopy } from "@/lib/app-copy";
import { useUiLanguage } from "@/lib/use-ui-language";
import { cn } from "@/lib/utils";

export function AppMenu() {
  const pathname = usePathname();
  const language = useUiLanguage();
  const copy = getAppCopy(language);
  const menuItems = [
    { href: "/", label: copy.nav.home, icon: Home },
    { href: "/visit-assistant", label: copy.nav.visitAssistant, icon: CalendarHeart },
    { href: "/appointments", label: copy.nav.appointments, icon: ClipboardPlus },
    { href: "/records", label: copy.nav.notes, icon: BookText },
    { href: "/agent-graph", label: copy.nav.agentGraph, icon: Workflow },
    { href: "/profile", label: copy.nav.profile, icon: UserRound },
  ];

  return (
    <div className="sticky top-0 z-[60] border-b border-slate-200/70 bg-[rgba(249,250,251,0.78)] backdrop-blur-xl">
      <div className="mx-auto flex w-full max-w-7xl items-center justify-between px-4 py-4 sm:px-6 lg:px-8">
        <Link href="/" className="inline-flex items-center gap-3 text-slate-950">
          <span className="flex h-10 w-10 items-center justify-center overflow-hidden rounded-2xl bg-white shadow-[0_12px_30px_rgba(15,23,42,0.15)] ring-1 ring-slate-200">
            <Image src="/logo.png" alt="Severity logo" width={40} height={40} className="h-full w-full object-cover" priority />
          </span>
          <span>
            <span className="block text-sm font-semibold tracking-[-0.02em]">Severity</span>
            <span className="block text-xs text-slate-500">{copy.nav.tagline}</span>
          </span>
        </Link>

        <nav className="flex items-center gap-2 rounded-full border border-slate-200 bg-white/85 p-1 shadow-[0_16px_45px_rgba(148,163,184,0.16)]">
          {menuItems.map((item) => {
            const Icon = item.icon;
            const active = pathname === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "inline-flex items-center gap-2 rounded-full px-4 py-2 text-sm font-medium transition",
                  active ? "bg-slate-950 text-white" : "text-slate-600 hover:bg-slate-100 hover:text-slate-950",
                )}
              >
                <Icon className="h-4 w-4" />
                {item.label}
              </Link>
            );
          })}
        </nav>
      </div>
    </div>
  );
}
