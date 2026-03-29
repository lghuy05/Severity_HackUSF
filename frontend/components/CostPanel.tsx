import { Clock3, CreditCard, ShieldCheck } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import type { CostOption, RiskLevel } from "@shared/types";

type CostPanelProps = {
  costOptions: CostOption[];
  riskLevel?: RiskLevel;
};

export function CostPanel({ costOptions, riskLevel }: CostPanelProps) {
  return (
    <Card className="animate-fade-in">
      <CardHeader className="border-b border-white/[0.08] pb-4">
        <div className="flex items-center justify-between gap-4">
          <div>
            <p className="text-xs uppercase tracking-[0.24em] text-slate-500">Cost</p>
            <CardTitle className="mt-1 text-xl">Compare care options</CardTitle>
            <CardDescription className="mt-2">
              Estimated pricing and wait times are shown only after urgency is understood.
            </CardDescription>
          </div>
          {riskLevel === "high" ? <Badge variant="danger">Escalated</Badge> : <Badge variant="safe">Cost-aware</Badge>}
        </div>
      </CardHeader>
      <CardContent className="space-y-3 pt-6">
        {costOptions.map((option) => {
          return (
            <div
              key={`${option.provider}-${option.care_type}-${option.estimated_cost}`}
              className="grid gap-4 rounded-[24px] border border-white/10 bg-white/[0.04] px-4 py-4 md:grid-cols-[1.4fr,0.8fr,0.8fr,0.9fr]"
            >
              <div>
                <p className="text-sm font-medium text-white">{option.provider}</p>
                <p className="mt-1 text-sm text-slate-300">{option.care_type}</p>
                <p className="mt-2 text-xs text-slate-400">{option.notes}</p>
              </div>
              <div className="flex items-center gap-2 text-sm text-slate-200">
                <CreditCard className="h-4 w-4 text-sky-300" />
                {option.estimated_cost}
              </div>
              <div className="flex items-center gap-2 text-sm text-slate-200">
                <Clock3 className="h-4 w-4 text-violet-300" />
                {option.estimated_wait ?? "Unknown"}
              </div>
              <div className="flex items-center gap-2 text-sm text-slate-200">
                <ShieldCheck className="h-4 w-4 text-emerald-300" />
                {option.coverage_summary ?? "Coverage varies"}
              </div>
            </div>
          );
        })}
      </CardContent>
    </Card>
  );
}
