"use client";

import type { AgentStep } from "../../shared/types";

type AgentFlowPanelProps = {
  steps: AgentStep[];
  visible: boolean;
};

export function AgentFlowPanel({ steps, visible }: AgentFlowPanelProps) {
  return (
    <aside
      className={[
        "fixed right-4 top-4 z-30 w-[min(320px,calc(100vw-2rem))] rounded-[28px] border border-white/12 bg-white/8 p-4 shadow-panel backdrop-blur-2xl transition-all duration-500 md:right-8 md:top-8",
        visible ? "translate-y-0 opacity-100" : "pointer-events-none -translate-y-4 opacity-0",
      ].join(" ")}
    >
      <div className="flex items-center justify-between">
        <div>
          <p className="text-[11px] font-semibold uppercase tracking-[0.28em] text-slate-400">Agent Flow</p>
          <h2 className="mt-1 text-base font-semibold text-white">Live reasoning</h2>
        </div>
        <span className="rounded-full border border-white/12 bg-white/6 px-3 py-1 text-[11px] font-medium text-slate-300">
          Active
        </span>
      </div>

      <div className="mt-4 space-y-2.5">
        {steps.map((step) => (
          <div
            key={step.key}
            className={[
              "flex items-start gap-3 rounded-2xl border p-3 transition-all duration-300",
              step.status === "running"
                ? "border-sky-400/30 bg-sky-400/12 shadow-[0_0_30px_rgba(56,189,248,0.15)]"
                : step.status === "done"
                  ? "border-emerald-400/20 bg-emerald-400/8"
                  : "border-white/8 bg-white/[0.03]",
            ].join(" ")}
          >
            <div
              className={[
                "mt-0.5 h-3 w-3 rounded-full transition-all duration-300",
                step.status === "done" ? "bg-emerald-300 shadow-[0_0_16px_rgba(110,231,183,0.65)]" : "",
                step.status === "running" ? "animate-agent-pulse bg-sky-300 shadow-[0_0_22px_rgba(125,211,252,0.8)]" : "",
                step.status === "idle" ? "bg-slate-600" : "",
              ].join(" ")}
            />
            <div>
              <p className="font-medium text-white">{step.label}</p>
              <p className="text-sm text-slate-400">
                {step.detail ?? (step.status === "idle" ? "Waiting" : step.status === "running" ? "Processing" : "Completed")}
              </p>
            </div>
          </div>
        ))}
      </div>
    </aside>
  );
}
