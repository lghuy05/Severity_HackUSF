"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Menu, UserRound, FolderClock, Home, X } from "lucide-react";
import { useEffect, useRef, useState } from "react";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

const MENU_ITEMS = [
  { href: "/", label: "Home", icon: Home, description: "Guided AI experience" },
  { href: "/records", label: "Past Records", icon: FolderClock, description: "Empty state for now" },
  { href: "/profile", label: "Profile", icon: UserRound, description: "Mock editable profile" },
];

export function AppMenu() {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    function handlePointerDown(event: MouseEvent) {
      if (!containerRef.current?.contains(event.target as Node)) {
        setOpen(false);
      }
    }

    function handleEscape(event: KeyboardEvent) {
      if (event.key === "Escape") {
        setOpen(false);
      }
    }

    window.addEventListener("mousedown", handlePointerDown);
    window.addEventListener("keydown", handleEscape);
    return () => {
      window.removeEventListener("mousedown", handlePointerDown);
      window.removeEventListener("keydown", handleEscape);
    };
  }, []);

  useEffect(() => {
    setOpen(false);
  }, [pathname]);

  return (
    <div ref={containerRef} className="fixed right-4 top-4 z-[60] sm:right-6 sm:top-6">
      <Button
        type="button"
        variant="secondary"
        size="icon"
        onClick={() => setOpen((current) => !current)}
        className="h-12 w-12 rounded-full border-white/[0.12] bg-[#11192a]/80 shadow-[0_18px_50px_rgba(6,10,24,0.35)]"
        aria-label={open ? "Close menu" : "Open menu"}
      >
        {open ? <X className="h-4.5 w-4.5" /> : <Menu className="h-4.5 w-4.5" />}
      </Button>

      <div
        className={cn(
          "absolute right-0 top-16 w-[300px] origin-top-right rounded-[28px] border border-white/[0.10] bg-[#0e1524]/92 p-3 shadow-[0_30px_80px_rgba(5,9,24,0.44)] backdrop-blur-2xl transition-all duration-200",
          open ? "pointer-events-auto translate-y-0 opacity-100" : "pointer-events-none -translate-y-2 opacity-0",
        )}
      >
        <div className="px-3 pb-3 pt-2">
          <p className="text-[11px] uppercase tracking-[0.24em] text-slate-500">Navigation</p>
          <p className="mt-1 text-sm text-slate-300">Switch between the guided flow and supporting pages.</p>
        </div>

        <div className="space-y-1">
          {MENU_ITEMS.map((item) => {
            const Icon = item.icon;
            const active = pathname === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "flex items-start gap-3 rounded-[20px] px-3 py-3 transition",
                  active ? "bg-white/[0.08] text-white" : "text-slate-300 hover:bg-white/[0.06] hover:text-white",
                )}
              >
                <div
                  className={cn(
                    "mt-0.5 flex h-10 w-10 items-center justify-center rounded-2xl border",
                    active ? "border-sky-300/[0.30] bg-sky-400/[0.12] text-sky-100" : "border-white/[0.10] bg-white/[0.04]",
                  )}
                >
                  <Icon className="h-4 w-4" />
                </div>
                <div className="min-w-0">
                  <p className="text-sm font-medium">{item.label}</p>
                  <p className="mt-1 text-xs leading-5 text-slate-400">{item.description}</p>
                </div>
              </Link>
            );
          })}
        </div>
      </div>
    </div>
  );
}
