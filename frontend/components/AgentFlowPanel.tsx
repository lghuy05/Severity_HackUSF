import { AgentGraphPanel } from "@/components/AgentGraphPanel";
import type { LatestContext } from "@/lib/latest-analysis";
import type { AnalyzeResponse, AgentStep } from "@shared/types";

type AgentFlowPanelProps = {
  steps: AgentStep[];
  analysis?: AnalyzeResponse | null;
  context?: LatestContext | null;
  visible: boolean;
};

export function AgentFlowPanel({ steps, analysis, context, visible }: AgentFlowPanelProps) {
  if (!visible || !steps.length || !analysis) {
    return null;
  }

  return <AgentGraphPanel steps={steps} analysis={analysis} context={context ?? null} visible={visible} />;
}
