import { CheckCircle2, CircleDashed, Wrench } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import type { AgentStep } from "@shared/types";

type AgentFlowPanelProps = {
  steps: AgentStep[];
  visible: boolean;
};

function statusVariant(status: AgentStep["status"]) {
  if (status === "done") {
    return "safe" as const;
  }
  if (status === "running") {
    return "default" as const;
  }
  return "warning" as const;
}

export function AgentFlowPanel({ steps, visible }: AgentFlowPanelProps) {
  if (!visible || !steps.length) {
    return null;
  }

  return (
    <div className="space-y-6">
      <div>
        <p className="text-xs uppercase tracking-[0.24em] text-slate-400">System flow</p>
        <h1 className="mt-2 text-4xl font-semibold tracking-[-0.04em] text-slate-950">Agent execution</h1>
        <p className="mt-3 max-w-2xl text-base leading-7 text-slate-600">
          This view is for demos and judges. It shows the backend agent sequence, each step summary, and the tools used.
        </p>
      </div>

      <div className="relative ml-3 space-y-5 before:absolute before:bottom-4 before:left-[15px] before:top-4 before:w-px before:bg-slate-200">
        {steps.map((step) => {
          const done = step.status === "done";
          return (
            <div key={step.agent} className="relative pl-12">
              <div
                className={cn(
                  "absolute left-0 top-7 flex h-8 w-8 items-center justify-center rounded-full border bg-white shadow-[0_8px_25px_rgba(148,163,184,0.14)]",
                  done ? "border-emerald-200 text-emerald-600" : "border-slate-200 text-slate-400",
                )}
              >
                {done ? <CheckCircle2 className="h-4.5 w-4.5" /> : <CircleDashed className="h-4.5 w-4.5" />}
              </div>

              <Card className="p-6">
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div>
                    <p className="text-sm font-semibold text-slate-950">{step.label}</p>
                    <p className="mt-2 text-sm leading-7 text-slate-600">{step.summary}</p>
                  </div>
                  <Badge variant={statusVariant(step.status)}>{step.status}</Badge>
                </div>

                {step.tools.length ? (
                  <div className="mt-4 flex flex-wrap gap-2">
                    {step.tools.map((tool) => (
                      <span
                        key={`${step.agent}-${tool}`}
                        className="inline-flex items-center gap-1 rounded-full border border-slate-200 bg-slate-50 px-2.5 py-1 text-[11px] uppercase tracking-[0.12em] text-slate-500"
                      >
                        <Wrench className="h-3 w-3" />
                        {tool}
                      </span>
                    ))}
                  </div>
                ) : null}
              </Card>
            </div>
          );
        })}
      </div>
    </div>
  );
}
