"use client";

import type { AgentStep } from "../../shared/types";

type AgentFlowPanelProps = {
  steps: AgentStep[];
};

export function AgentFlowPanel({ steps }: AgentFlowPanelProps) {
  return (
    <div className="rounded-[28px] bg-white/90 p-5 shadow-panel backdrop-blur">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.24em] text-slate-500">Agent Flow</p>
          <h2 className="mt-1 text-xl font-semibold text-ink">Voice Agent to Navigation Agent</h2>
        </div>
        <span className="rounded-full bg-mist px-3 py-1 text-xs font-medium text-slate-600">
          Live reasoning
        </span>
      </div>

      <div className="mt-5 space-y-3">
        {steps.map((step) => (
          <div
            key={step.key}
            className="flex items-start gap-3 rounded-2xl border border-slate-100 bg-slate-50/90 p-3"
          >
            <div
              className={[
                "mt-0.5 h-3 w-3 rounded-full",
                step.status === "done" ? "bg-aqua" : "",
                step.status === "running" ? "bg-coral animate-pulse" : "",
                step.status === "idle" ? "bg-slate-300" : "",
              ].join(" ")}
            />
            <div>
              <p className="font-medium text-ink">{step.label}</p>
              <p className="text-sm text-slate-500">
                {step.detail ?? (step.status === "idle" ? "Waiting" : step.status === "running" ? "Processing" : "Completed")}
              </p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
