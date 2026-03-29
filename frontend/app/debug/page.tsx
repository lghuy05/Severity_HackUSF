"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { AgentFlowPanel } from "@/components/AgentFlowPanel";
import { Button } from "@/components/ui/button";
import { loadLatestAnalysis } from "@/lib/latest-analysis";
import type { AnalyzeResponse } from "@shared/types";

export default function DebugPage() {
  const [analysis, setAnalysis] = useState<AnalyzeResponse | null>(null);

  useEffect(() => {
    setAnalysis(loadLatestAnalysis());
  }, []);

  return (
    <main className="min-h-screen bg-[linear-gradient(180deg,#f8fafc_0%,#f1f5f9_100%)]">
      <div className="mx-auto w-full max-w-5xl px-4 py-10 sm:px-6 lg:px-8">
        {analysis ? (
          <AgentFlowPanel steps={analysis.agent_flow} visible />
        ) : (
          <div className="mx-auto max-w-2xl rounded-[36px] border border-slate-200 bg-white p-10 text-center shadow-[0_30px_80px_rgba(148,163,184,0.12)]">
            <h1 className="text-4xl font-semibold tracking-[-0.04em] text-slate-950">No execution trace yet</h1>
            <p className="mt-4 text-base leading-8 text-slate-600">
              Run a symptom check from the main experience first. The system view will appear here once the backend
              returns an agent flow.
            </p>
            <div className="mt-8">
              <Button asChild>
                <Link href="/">Go to main experience</Link>
              </Button>
            </div>
          </div>
        )}
      </div>
    </main>
  );
}
