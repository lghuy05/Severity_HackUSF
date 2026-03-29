"use client";

import { useMemo } from "react";
import {
  Background,
  Controls,
  type Edge,
  Handle,
  MarkerType,
  MiniMap,
  Position,
  ReactFlow,
  type Node,
  type NodeProps,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import { Bot, BrainCircuit, CheckCircle2, GitBranch, Sparkles, Wrench } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import type { AnalyzeResponse, AgentStep } from "@shared/types";
import type { LatestContext } from "@/lib/latest-analysis";

type GraphNodeKind = "input" | "semantic" | "decision" | "agent" | "output";

type GraphNodeData = {
  kind: GraphNodeKind;
  title: string;
  subtitle: string;
  body: string;
  tools?: string[];
  status?: AgentStep["status"];
};

type AgentGraphPanelProps = {
  steps: AgentStep[];
  analysis: AnalyzeResponse;
  context: LatestContext | null;
  visible: boolean;
};

function statusVariant(status?: AgentStep["status"]) {
  if (status === "done") {
    return "safe" as const;
  }
  if (status === "running") {
    return "default" as const;
  }
  return "warning" as const;
}

function GraphCardNode({ data }: NodeProps<Node<GraphNodeData>>) {
  const Icon =
    data.kind === "input"
      ? Sparkles
      : data.kind === "semantic"
        ? BrainCircuit
        : data.kind === "decision"
          ? GitBranch
          : data.kind === "output"
            ? CheckCircle2
            : Bot;

  return (
    <div
      className={cn(
        "min-w-[260px] max-w-[300px] rounded-[28px] border bg-white/95 p-4 shadow-[0_20px_60px_rgba(148,163,184,0.18)] backdrop-blur-xl",
        data.kind === "input" && "border-sky-200",
        data.kind === "semantic" && "border-violet-200",
        data.kind === "decision" && "border-amber-200",
        data.kind === "agent" && "border-emerald-200",
        data.kind === "output" && "border-slate-200",
      )}
    >
      <Handle type="target" position={Position.Left} className="!h-3 !w-3 !border-2 !border-white !bg-slate-400" />
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-start gap-3">
          <div
            className={cn(
              "mt-0.5 flex h-10 w-10 items-center justify-center rounded-2xl",
              data.kind === "input" && "bg-sky-50 text-sky-600",
              data.kind === "semantic" && "bg-violet-50 text-violet-600",
              data.kind === "decision" && "bg-amber-50 text-amber-600",
              data.kind === "agent" && "bg-emerald-50 text-emerald-600",
              data.kind === "output" && "bg-slate-100 text-slate-700",
            )}
          >
            <Icon className="h-5 w-5" />
          </div>
          <div>
            <p className="text-[11px] uppercase tracking-[0.18em] text-slate-400">{data.kind}</p>
            <p className="mt-1 text-base font-semibold text-slate-950">{data.title}</p>
            <p className="mt-1 text-sm text-slate-500">{data.subtitle}</p>
          </div>
        </div>
        {data.status ? <Badge variant={statusVariant(data.status)}>{data.status}</Badge> : null}
      </div>

      <p className="mt-4 text-sm leading-6 text-slate-700">{data.body}</p>

      {data.tools?.length ? (
        <div className="mt-4 flex flex-wrap gap-2">
          {data.tools.map((tool) => (
            <span
              key={`${data.title}-${tool}`}
              className="inline-flex items-center gap-1 rounded-full border border-slate-200 bg-slate-50 px-2.5 py-1 text-[11px] uppercase tracking-[0.12em] text-slate-500"
            >
              <Wrench className="h-3 w-3" />
              {tool}
            </span>
          ))}
        </div>
      ) : null}
      <Handle type="source" position={Position.Right} className="!h-3 !w-3 !border-2 !border-white !bg-slate-400" />
    </div>
  );
}

const nodeTypes = {
  input: GraphCardNode,
  semantic: GraphCardNode,
  decision: GraphCardNode,
  agent: GraphCardNode,
  output: GraphCardNode,
};

function buildOutputBody(analysis: AnalyzeResponse): string {
  const outputs: string[] = [];
  if (analysis.navigation.hospitals.length) {
    outputs.push(`${analysis.navigation.hospitals.length} care options`);
  }
  if (analysis.cost_options.length) {
    outputs.push(`${analysis.cost_options.length} cost estimates`);
  }
  if (analysis.provider_message) {
    outputs.push("provider-ready summary");
  }
  if (analysis.emergency_flag) {
    outputs.push("emergency guidance");
  }

  return outputs.length ? `Generated ${outputs.join(", ")}.` : "Prepared the assistant response and updated the patient session state.";
}

function buildGraph({
  steps,
  analysis,
  context,
}: {
  steps: AgentStep[];
  analysis: AnalyzeResponse;
  context: LatestContext | null;
}): { nodes: Array<Node<GraphNodeData>>; edges: Edge[] } {
  const totalAgents = Math.max(steps.length, 1);
  const topOffset = 120;
  const verticalGap = 190;
  const centerY = topOffset + ((totalAgents - 1) * verticalGap) / 2;

  const nodes: Array<Node<GraphNodeData>> = [
    {
      id: "input",
      type: "input",
      position: { x: 0, y: centerY },
      data: {
        kind: "input",
        title: "User Input",
        subtitle: context?.location ? `Location: ${context.location}` : "Latest patient message",
        body: context?.text || analysis.summary.patient_input || "No saved patient input available.",
      },
    },
    {
      id: "semantic",
      type: "semantic",
      position: { x: 340, y: centerY - 150 },
      data: {
        kind: "semantic",
        title: "Semantic Understanding",
        subtitle: `Detected language: ${(analysis.language_output.detected_language || "en").toUpperCase()}`,
        body: analysis.summary.normalized_text || analysis.language_output.simplified_text || "The system normalized the user message and extracted clinically relevant meaning.",
      },
    },
    {
      id: "decision",
      type: "decision",
      position: { x: 690, y: centerY },
      data: {
        kind: "decision",
        title: "Decision Node",
        subtitle: `Risk: ${analysis.triage.risk_level.toUpperCase()}`,
        body: steps.length > 1
          ? `The root coordinator branched into ${steps.length} agent paths based on urgency, care routing, and available tools.`
          : "The coordinator selected the next specialist path based on urgency and requested outcome.",
      },
    },
    {
      id: "output",
      type: "output",
      position: { x: 1380, y: centerY },
      data: {
        kind: "output",
        title: "Outputs",
        subtitle: analysis.navigation.recommendation || "Assistant response ready",
        body: buildOutputBody(analysis),
      },
    },
  ];

  const edges: Edge[] = [
    {
      id: "input-semantic",
      source: "input",
      target: "semantic",
      markerEnd: { type: MarkerType.ArrowClosed },
      animated: true,
      style: { stroke: "#38bdf8", strokeWidth: 2.5 },
    },
    {
      id: "semantic-decision",
      source: "semantic",
      target: "decision",
      markerEnd: { type: MarkerType.ArrowClosed },
      animated: true,
      style: { stroke: "#8b5cf6", strokeWidth: 2.5 },
    },
  ];

  if (!steps.length) {
    edges.push({
      id: "decision-output",
      source: "decision",
      target: "output",
      markerEnd: { type: MarkerType.ArrowClosed },
      animated: true,
      style: { stroke: "#94a3b8", strokeWidth: 2.5 },
    });
    return { nodes, edges };
  }

  steps.forEach((step, index) => {
    const y = topOffset + index * verticalGap;
    const nodeId = `agent-${index}`;
    nodes.push({
      id: nodeId,
      type: "agent",
      position: { x: 1020, y },
      data: {
        kind: "agent",
        title: step.label,
        subtitle: step.agent,
        body: step.summary,
        tools: step.tools,
        status: step.status,
      },
    });

    edges.push(
      {
        id: `decision-${nodeId}`,
        source: "decision",
        target: nodeId,
        label: index === 0 ? "primary path" : "parallel path",
        markerEnd: { type: MarkerType.ArrowClosed },
        animated: step.status === "running",
        style: { stroke: "#10b981", strokeWidth: 2.5 },
        labelStyle: { fill: "#64748b", fontSize: 12 },
      },
      {
        id: `${nodeId}-output`,
        source: nodeId,
        target: "output",
        markerEnd: { type: MarkerType.ArrowClosed },
        animated: step.status === "running",
        style: { stroke: "#94a3b8", strokeWidth: 2 },
      },
    );
  });

  return { nodes, edges };
}

export function AgentGraphPanel({ steps, analysis, context, visible }: AgentGraphPanelProps) {
  const graph = useMemo(() => buildGraph({ steps, analysis, context }), [analysis, context, steps]);

  if (!visible) {
    return null;
  }

  return (
    <div className="space-y-6">
      <div>
        <p className="text-xs uppercase tracking-[0.24em] text-slate-400">System graph</p>
        <h1 className="mt-2 text-4xl font-semibold tracking-[-0.04em] text-slate-950">Agent Graph</h1>
        <p className="mt-3 max-w-3xl text-base leading-7 text-slate-600">
          This graph visualizes semantic understanding, branching decisions, agent specialization, and tool usage from the existing frontend trace.
        </p>
      </div>

      <Card className="overflow-hidden">
        <CardHeader className="border-b border-slate-200/80 pb-4">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <CardTitle className="text-2xl tracking-[-0.03em]">Dynamic reasoning graph</CardTitle>
              <CardDescription className="mt-2">
                Judges can pan, zoom, and inspect each branch to see which specialist agent contributed and which tools were invoked.
              </CardDescription>
            </div>
            <div className="flex flex-wrap gap-2">
              <Badge>Input</Badge>
              <Badge>Semantic</Badge>
              <Badge>Decision</Badge>
              <Badge>Agent</Badge>
              <Badge variant="safe">Output</Badge>
            </div>
          </div>
        </CardHeader>
        <CardContent className="p-0">
          <div className="h-[760px] w-full bg-[radial-gradient(circle_at_top,rgba(56,189,248,0.08),transparent_28%),linear-gradient(180deg,#f8fafc_0%,#eef2ff_100%)]">
            <ReactFlow
              nodes={graph.nodes}
              edges={graph.edges}
              nodeTypes={nodeTypes}
              fitView
              fitViewOptions={{ padding: 0.12 }}
              nodesDraggable={false}
              nodesConnectable={false}
              elementsSelectable
              proOptions={{ hideAttribution: true }}
            >
              <MiniMap
                pannable
                zoomable
                nodeColor={(node) => {
                  if (node.type === "input") return "#38bdf8";
                  if (node.type === "semantic") return "#8b5cf6";
                  if (node.type === "decision") return "#f59e0b";
                  if (node.type === "agent") return "#10b981";
                  return "#334155";
                }}
                className="!bg-white/90"
              />
              <Controls position="bottom-right" />
              <Background gap={28} size={1} color="#dbe4f0" />
            </ReactFlow>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
