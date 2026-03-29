"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { ActivitySquare, CalendarHeart, Home, UserRound, Workflow } from "lucide-react";
import { cn } from "@/lib/utils";

const MENU_ITEMS = [
  { href: "/", label: "Home", icon: Home },
  { href: "/visit-assistant", label: "Visit assistant", icon: CalendarHeart },
  { href: "/profile", label: "Profile", icon: UserRound },
  { href: "/debug", label: "System view", icon: Workflow },
];

export function AppMenu() {
  const pathname = usePathname();

  return (
    <div className="sticky top-0 z-[60] border-b border-slate-200/70 bg-[rgba(249,250,251,0.78)] backdrop-blur-xl">
      <div className="mx-auto flex w-full max-w-7xl items-center justify-between px-4 py-4 sm:px-6 lg:px-8">
        <Link href="/" className="inline-flex items-center gap-3 text-slate-950">
          <span className="flex h-10 w-10 items-center justify-center rounded-2xl bg-slate-950 text-white shadow-[0_12px_30px_rgba(15,23,42,0.15)]">
            <ActivitySquare className="h-4.5 w-4.5" />
          </span>
          <span>
            <span className="block text-sm font-semibold tracking-[-0.02em]">Severity</span>
            <span className="block text-xs text-slate-500">Guided care navigation</span>
          </span>
        </Link>

        <nav className="flex items-center gap-2 rounded-full border border-slate-200 bg-white/85 p-1 shadow-[0_16px_45px_rgba(148,163,184,0.16)]">
          {MENU_ITEMS.map((item) => {
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
