import { AudioLines, Languages, MapPinned, Stethoscope, Zap } from "lucide-react";

import { cn } from "@/lib/utils";

const FLOW_ITEMS = [
  { key: "voice", label: "Voice", icon: AudioLines },
  { key: "language", label: "Language", icon: Languages },
  { key: "triage", label: "Triage", icon: Stethoscope },
  { key: "navigation", label: "Navigation", icon: MapPinned },
  { key: "action", label: "Action", icon: Zap },
] as const;

type AgentFlowProps = {
  activeStep: string;
  visible: boolean;
};

export function AgentFlow({ activeStep, visible }: AgentFlowProps) {
  if (!visible) {
    return null;
  }

  const activeIndex = FLOW_ITEMS.findIndex((item) => item.key === activeStep);

  return (
    <div className="pointer-events-none fixed left-1/2 top-6 z-40 w-[min(92vw,820px)] -translate-x-1/2 animate-fade-in">
      <div className="rounded-full border border-white/[0.12] bg-[#0e1422]/72 px-3 py-3 shadow-[0_20px_60px_rgba(5,9,24,0.42)] backdrop-blur-2xl">
        <div className="flex items-center justify-between gap-2 overflow-x-auto">
          {FLOW_ITEMS.map((item, index) => {
            const Icon = item.icon;
            const isActive = index === activeIndex;
            const isComplete = index < activeIndex;

            return (
              <div key={item.key} className="flex min-w-[120px] items-center gap-3 px-2 py-1">
                <div
                  className={cn(
                    "flex h-10 w-10 items-center justify-center rounded-full border transition-all duration-300",
                    isActive && "border-emerald-300/[0.50] bg-emerald-400/[0.16] text-emerald-200 shadow-[0_0_24px_rgba(74,222,128,0.18)]",
                    isComplete && "border-sky-300/[0.30] bg-sky-400/[0.14] text-sky-100",
                    !isActive && !isComplete && "border-white/10 bg-white/[0.06] text-slate-400",
                  )}
                >
                  <Icon className={cn("h-4 w-4", isActive && "animate-agent-pulse")} />
                </div>
                <div className="min-w-0">
                  <p className="text-[11px] uppercase tracking-[0.22em] text-slate-500">Agent</p>
                  <p className={cn("text-sm font-medium", isActive || isComplete ? "text-white" : "text-slate-400")}>
                    {item.label}
                  </p>
                </div>
                {index < FLOW_ITEMS.length - 1 ? (
                  <div className={cn("hidden h-px flex-1 md:block", isComplete ? "bg-sky-300/[0.40]" : "bg-white/[0.08]")} />
                ) : null}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
