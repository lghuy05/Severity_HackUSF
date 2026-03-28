import { Clock3, CreditCard, ShieldCheck } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import type { HospitalLocation, RiskLevel } from "@shared/types";

type CostPanelProps = {
  hospitals: HospitalLocation[];
  riskLevel?: RiskLevel;
};

const MOCK_COSTS = [
  { estimate: "$180", wait: "22 min", coverage: "In-network" },
  { estimate: "$240", wait: "14 min", coverage: "Partial" },
  { estimate: "$95", wait: "35 min", coverage: "Community pricing" },
];

export function CostPanel({ hospitals, riskLevel }: CostPanelProps) {
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
        {hospitals.map((hospital, index) => {
          const detail = MOCK_COSTS[index] ?? MOCK_COSTS[MOCK_COSTS.length - 1];
          return (
            <div
              key={`${hospital.name}-${hospital.address}-cost`}
              className="grid gap-4 rounded-[24px] border border-white/10 bg-white/[0.04] px-4 py-4 md:grid-cols-[1.4fr,0.8fr,0.8fr,0.9fr]"
            >
              <div>
                <p className="text-sm font-medium text-white">{hospital.name}</p>
                <p className="mt-1 text-sm text-slate-300">{hospital.address}</p>
              </div>
              <div className="flex items-center gap-2 text-sm text-slate-200">
                <CreditCard className="h-4 w-4 text-sky-300" />
                {detail.estimate}
              </div>
              <div className="flex items-center gap-2 text-sm text-slate-200">
                <Clock3 className="h-4 w-4 text-violet-300" />
                {detail.wait}
              </div>
              <div className="flex items-center gap-2 text-sm text-slate-200">
                <ShieldCheck className="h-4 w-4 text-emerald-300" />
                {detail.coverage}
              </div>
            </div>
          );
        })}
      </CardContent>
    </Card>
  );
}
