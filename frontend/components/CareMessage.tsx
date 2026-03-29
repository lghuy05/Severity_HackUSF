"use client";

import { AlertTriangle, ArrowRight, HeartPulse, MapPinned, ShieldCheck } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import type { AnalyzeResponse, RiskLevel } from "@shared/types";

type CareMessageProps = {
  analysis: AnalyzeResponse;
  copy: {
    guidanceEyebrow: string;
    guidanceTitle: string;
    understandingLabel: string;
    recommendedActionLabel: string;
    nextStepsLabel: string;
    describedAs: (text: string) => string;
    actionHigh: string;
    actionNormal: (recommendation: string) => string;
    nextSteps: (analysis: AnalyzeResponse) => string[];
  };
};

function riskVariant(riskLevel: RiskLevel) {
  if (riskLevel === "high") {
    return "danger" as const;
  }
  if (riskLevel === "medium") {
    return "warning" as const;
  }
  return "safe" as const;
}

function buildActionText(
  analysis: AnalyzeResponse,
  copy: {
    actionHigh: string;
    actionNormal: (recommendation: string) => string;
  },
) {
  if (analysis.emergency_flag || analysis.triage.risk_level === "high") {
    return copy.actionHigh;
  }
  return copy.actionNormal(analysis.navigation.recommendation);
}

export function CareMessage({ analysis, copy }: CareMessageProps) {
  const nextSteps = copy.nextSteps(analysis);

  return (
    <Card className="rounded-[36px] p-8">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-xs uppercase tracking-[0.24em] text-slate-400">{copy.guidanceEyebrow}</p>
          <h2 className="mt-2 text-3xl font-semibold text-slate-950">{copy.guidanceTitle}</h2>
        </div>
        <Badge variant={riskVariant(analysis.triage.risk_level)}>{analysis.triage.risk_level} risk</Badge>
      </div>

      <div className="mt-8 grid gap-4">
        <div className="rounded-[28px] border border-slate-200 bg-slate-50/80 p-6">
          <div className="flex items-center gap-2 text-sm font-medium text-slate-950">
            <HeartPulse className="h-4 w-4 text-sky-300" />
            {copy.understandingLabel}
          </div>
          <p className="mt-3 text-sm leading-7 text-slate-700">
            {copy.describedAs(analysis.language_output.simplified_text)}
          </p>
        </div>

        <div className="rounded-[28px] border border-slate-200 bg-slate-50/80 p-6">
          <div className="flex items-center gap-2 text-sm font-medium text-slate-950">
            {analysis.triage.risk_level === "high" ? (
              <AlertTriangle className="h-4 w-4 text-rose-300" />
            ) : (
              <ShieldCheck className="h-4 w-4 text-emerald-300" />
            )}
            {copy.recommendedActionLabel}
          </div>
          <p className="mt-3 text-sm leading-7 text-slate-700">{buildActionText(analysis, copy)}</p>
        </div>

        {nextSteps.length > 0 ? (
          <div className="rounded-[28px] border border-slate-200 bg-slate-50/80 p-6">
            <div className="flex items-center gap-2 text-sm font-medium text-slate-950">
              <MapPinned className="h-4 w-4 text-cyan-300" />
              {copy.nextStepsLabel}
            </div>
            <div className="mt-3 space-y-3">
              {nextSteps.map((step) => (
                <div key={step} className="flex items-start gap-3 text-sm leading-7 text-slate-700">
                  <ArrowRight className="mt-1 h-4 w-4 shrink-0 text-slate-400" />
                  <p>{step}</p>
                </div>
              ))}
            </div>
          </div>
        ) : null}
      </div>
    </Card>
  );
}
