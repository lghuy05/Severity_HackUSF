"use client";

import type { ChatMessage } from "../../shared/types";

type ChatPanelProps = {
  messages: ChatMessage[];
};

export function ChatPanel({ messages }: ChatPanelProps) {
  return (
    <div className="rounded-[28px] bg-white/90 p-5 shadow-panel backdrop-blur">
      <p className="text-xs font-semibold uppercase tracking-[0.24em] text-slate-500">Conversation</p>
      <div className="mt-4 max-h-[360px] space-y-4 overflow-y-auto pr-2">
        {messages.map((message) => (
          <div
            key={message.id}
            className={[
              "max-w-[90%] rounded-3xl px-4 py-3 text-sm leading-6",
              message.role === "user" ? "ml-auto bg-ink text-white" : "bg-mist text-ink",
            ].join(" ")}
          >
            {message.content}
          </div>
        ))}
      </div>
    </div>
  );
}
