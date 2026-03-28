"use client";

import type { ChatMessage } from "../../shared/types";

type ChatProps = {
  messages: ChatMessage[];
  isTyping?: boolean;
  className?: string;
};

export function Chat({ messages, isTyping = false, className = "" }: ChatProps) {
  return (
    <section
      className={[
        "rounded-[32px] border border-white/10 bg-white/6 p-5 shadow-panel backdrop-blur-2xl",
        className,
      ].join(" ")}
    >
      <p className="text-[11px] font-semibold uppercase tracking-[0.3em] text-slate-500">Conversation</p>
      <div className="mt-5 space-y-4">
        {messages.map((message) => (
          <article
            key={message.id}
            className={[
              "max-w-[92%] rounded-[24px] px-4 py-3 text-sm leading-6 transition-all duration-300",
              message.role === "user"
                ? "ml-auto bg-gradient-to-r from-sky-500 to-indigo-500 text-white"
                : "border border-white/8 bg-white/5 text-slate-100",
            ].join(" ")}
          >
            {message.content}
          </article>
        ))}

        {isTyping ? (
          <div className="inline-flex items-center gap-2 rounded-full border border-white/8 bg-white/5 px-4 py-3 text-sm text-slate-300">
            <span className="typing-dot" />
            <span className="typing-dot [animation-delay:160ms]" />
            <span className="typing-dot [animation-delay:320ms]" />
            AI is composing the next step
          </div>
        ) : null}
      </div>
    </section>
  );
}
