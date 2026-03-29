"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { CareOptionsBoard } from "@/components/CareOptionsBoard";
import { Button } from "@/components/ui/button";
import { loadLatestAnalysis, loadLatestContext } from "@/lib/latest-analysis";
import type { AnalyzeResponse } from "@shared/types";

export default function CarePage() {
  const [analysis, setAnalysis] = useState<AnalyzeResponse | null>(null);
  const [location, setLocation] = useState("");

  useEffect(() => {
    setAnalysis(loadLatestAnalysis());
    setLocation(loadLatestContext()?.location ?? "");
  }, []);

  return (
    <main className="app-shell-gradient min-h-screen">
      <div className="mx-auto w-full max-w-6xl px-4 py-10 sm:px-6 lg:px-8">
        {analysis ? (
          <CareOptionsBoard analysis={analysis} />
        ) : (
          <div className="mx-auto max-w-2xl rounded-[36px] border border-slate-200 bg-white/90 p-10 text-center shadow-[0_30px_80px_rgba(148,163,184,0.12)]">
            <h1 className="text-4xl font-semibold tracking-[-0.04em] text-slate-950">No care options yet</h1>
            <p className="mt-4 text-base leading-8 text-slate-600">
              Start from the main experience so we can assess symptoms and find nearby care for
              {location ? ` ${location}` : " your location"}.
            </p>
            <div className="mt-8">
              <Button asChild>
                <Link href="/">Start on the main page</Link>
              </Button>
            </div>
          </div>
        )}
      </div>
    </main>
  );
}
