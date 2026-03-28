import { Bot, Sparkles } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import type { ChatMessage, RiskLevel } from "@shared/types";

type ChatViewProps = {
  messages: ChatMessage[];
  isTyping?: boolean;
  riskLevel?: RiskLevel;
  title?: string;
};

function riskVariant(riskLevel?: RiskLevel) {
  if (riskLevel === "high") {
    return "danger" as const;
  }
  if (riskLevel === "medium") {
    return "warning" as const;
  }
  if (riskLevel === "low") {
    return "safe" as const;
  }
  return "default" as const;
}

export function ChatView({ messages, isTyping = false, riskLevel, title = "Care guidance" }: ChatViewProps) {
  return (
    <section className="flex h-full min-h-[420px] flex-col rounded-[32px] border border-white/10 bg-white/[0.06] p-4 shadow-[0_24px_80px_rgba(4,9,22,0.38)] backdrop-blur-2xl">
      <div className="mb-4 flex items-center justify-between gap-4 px-2 pt-1">
        <div>
          <p className="text-xs uppercase tracking-[0.26em] text-slate-500">AI Navigator</p>
          <h2 className="mt-1 text-xl font-semibold text-white">{title}</h2>
        </div>
        {riskLevel ? <Badge variant={riskVariant(riskLevel)}>{riskLevel} risk</Badge> : null}
      </div>

      <div className="flex flex-1 flex-col gap-3 overflow-y-auto px-1 pb-1">
        {messages.map((message, index) => {
          const isAssistant = message.role === "assistant";
          return (
            <div
              key={message.id}
              className={cn("flex animate-fade-in", isAssistant ? "justify-start" : "justify-end")}
              style={{ animationDelay: `${index * 60}ms` }}
            >
              <div
                className={cn(
                  "max-w-[86%] rounded-[26px] px-4 py-3 text-sm leading-7 shadow-[0_14px_40px_rgba(5,9,24,0.22)]",
                  isAssistant
                    ? "border border-white/10 bg-[#11192a]/92 text-slate-100"
                    : "bg-[linear-gradient(135deg,rgba(59,130,246,0.85),rgba(129,140,248,0.9))] text-white",
                )}
              >
                {isAssistant ? (
                  <div className="mb-2 flex items-center gap-2 text-[11px] uppercase tracking-[0.18em] text-slate-400">
                    <Bot className="h-3.5 w-3.5" />
                    Assistant
                  </div>
                ) : null}
                <p>{message.content}</p>
              </div>
            </div>
          );
        })}

        {isTyping ? (
          <div className="flex animate-fade-in justify-start">
            <div className="rounded-[24px] border border-white/10 bg-[#11192a]/92 px-4 py-3 text-slate-300">
              <div className="mb-2 flex items-center gap-2 text-[11px] uppercase tracking-[0.18em] text-slate-400">
                <Sparkles className="h-3.5 w-3.5" />
                Thinking
              </div>
              <div className="flex items-center gap-1.5">
                <span className="typing-dot" />
                <span className="typing-dot [animation-delay:150ms]" />
                <span className="typing-dot [animation-delay:300ms]" />
              </div>
            </div>
          </div>
        ) : null}
      </div>
    </section>
  );
}
