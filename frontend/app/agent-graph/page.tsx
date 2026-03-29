"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { AgentGraphPanel } from "@/components/AgentGraphPanel";
import { Button } from "@/components/ui/button";
import { getAppCopy } from "@/lib/app-copy";
import { loadLatestAnalysis, loadLatestContext, type LatestContext } from "@/lib/latest-analysis";
import { useUiLanguage } from "@/lib/use-ui-language";
import type { AnalyzeResponse } from "@shared/types";

export default function AgentGraphPage() {
  const language = useUiLanguage();
  const copy = getAppCopy(language).graph;
  const [analysis, setAnalysis] = useState<AnalyzeResponse | null>(null);
  const [context, setContext] = useState<LatestContext | null>(null);

  useEffect(() => {
    setAnalysis(loadLatestAnalysis());
    setContext(loadLatestContext());
  }, []);

  return (
    <main className="min-h-screen bg-[linear-gradient(180deg,#f8fafc_0%,#eef2ff_100%)]">
      <div className="mx-auto w-full max-w-7xl px-4 py-10 sm:px-6 lg:px-8">
        {analysis ? (
          <AgentGraphPanel steps={analysis.agent_flow} analysis={analysis} context={context} visible />
        ) : (
          <div className="mx-auto max-w-2xl rounded-[36px] border border-slate-200 bg-white p-10 text-center shadow-[0_30px_80px_rgba(148,163,184,0.12)]">
            <h1 className="text-4xl font-semibold tracking-[-0.04em] text-slate-950">{copy.emptyTitle}</h1>
            <p className="mt-4 text-base leading-8 text-slate-600">{copy.emptyDescription}</p>
            <div className="mt-8">
              <Button asChild>
                <Link href="/">{copy.emptyCta}</Link>
              </Button>
            </div>
          </div>
        )}
      </div>
    </main>
  );
}
