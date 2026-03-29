import { Children, useEffect, useRef, type ReactNode } from "react";
import { Bot, Sparkles } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import type { ChatMessage, RiskLevel } from "@shared/types";

type ChatViewProps = {
  messages: ChatMessage[];
  isTyping?: boolean;
  riskLevel?: RiskLevel;
  title?: string;
  assistantLabel?: string;
  reviewingLabel?: string;
  embeddedMessages?: ReactNode[];
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

export function ChatView({
  messages,
  isTyping = false,
  riskLevel,
  title = "Care guidance",
  assistantLabel = "Care assistant",
  reviewingLabel = "Reviewing",
  embeddedMessages = [],
}: ChatViewProps) {
  const scrollRef = useRef<HTMLDivElement | null>(null);
  const visibleEmbeddedMessages = Children.toArray(embeddedMessages);

  useEffect(() => {
    const container = scrollRef.current;
    if (!container) {
      return;
    }

    container.scrollTo({
      top: container.scrollHeight,
      behavior: "smooth",
    });
  }, [messages, isTyping, visibleEmbeddedMessages.length]);

  return (
    <section className="flex h-full min-h-[360px] flex-col overflow-hidden rounded-[36px] border border-slate-200/80 bg-white/88 p-6 shadow-[0_28px_80px_rgba(148,163,184,0.16)] backdrop-blur-xl">
      <div className="mb-6 flex items-center justify-between gap-4">
        <div>
          <p className="text-xs uppercase tracking-[0.26em] text-slate-400">Conversation</p>
          <h2 className="mt-1 text-2xl font-semibold text-slate-950">{title}</h2>
        </div>
        {riskLevel ? <Badge variant={riskVariant(riskLevel)}>{riskLevel} risk</Badge> : null}
      </div>

      <div ref={scrollRef} className="flex flex-1 flex-col gap-4 overflow-y-auto pr-1">
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
                  "max-w-[86%] rounded-[28px] px-5 py-4 text-sm leading-7 shadow-[0_12px_30px_rgba(148,163,184,0.12)]",
                  isAssistant
                    ? "border border-slate-200 bg-slate-50 text-slate-700"
                    : "bg-[linear-gradient(135deg,#0f172a,#1e293b)] text-white",
                )}
              >
                {isAssistant ? (
                  <div className="mb-2 flex items-center gap-2 text-[11px] uppercase tracking-[0.18em] text-slate-400">
                    <Bot className="h-3.5 w-3.5" />
                    {assistantLabel}
                  </div>
                ) : null}
                <p className="whitespace-pre-line break-words">{message.content}</p>
              </div>
            </div>
          );
        })}

        {visibleEmbeddedMessages.map((content, index) => (
          <div key={`embedded-${index}`} className="flex animate-fade-in justify-start">
            <div className="w-full max-w-[92%] rounded-[28px] border border-slate-200 bg-slate-50 px-5 py-4 shadow-[0_12px_30px_rgba(148,163,184,0.12)]">
              <div className="mb-2 flex items-center gap-2 text-[11px] uppercase tracking-[0.18em] text-slate-400">
                <Bot className="h-3.5 w-3.5" />
                {assistantLabel}
              </div>
              {content}
            </div>
          </div>
        ))}

        {isTyping ? (
          <div className="flex animate-fade-in justify-start">
            <div className="rounded-[24px] border border-slate-200 bg-slate-50 px-4 py-3 text-slate-500">
              <div className="mb-2 flex items-center gap-2 text-[11px] uppercase tracking-[0.18em] text-slate-400">
                <Sparkles className="h-3.5 w-3.5" />
                {reviewingLabel}
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
