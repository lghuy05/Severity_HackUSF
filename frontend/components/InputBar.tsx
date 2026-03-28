"use client";

import { Loader2, Mic, SendHorizontal } from "lucide-react";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

type InputBarProps = {
  value: string;
  onChange: (value: string) => void;
  onSubmit: () => void;
  onVoiceToggle: () => void;
  isListening?: boolean;
  isBusy?: boolean;
  compact?: boolean;
};

export function InputBar({
  value,
  onChange,
  onSubmit,
  onVoiceToggle,
  isListening = false,
  isBusy = false,
  compact = false,
}: InputBarProps) {
  return (
    <div
      className={cn(
        "w-full rounded-full border border-white/[0.14] bg-white/[0.08] p-2 shadow-[0_24px_80px_rgba(6,10,24,0.38)] backdrop-blur-2xl transition-all duration-300",
        compact ? "max-w-3xl" : "max-w-4xl",
      )}
    >
      <div className="flex items-center gap-2 rounded-full bg-[#0d1320]/80 px-3 py-3">
        <Button
          type="button"
          variant="secondary"
          size="icon"
          onClick={onVoiceToggle}
          className={cn(
            "shrink-0 rounded-full border-white/[0.12]",
            isListening && "border-emerald-400/[0.40] bg-emerald-500/[0.16] text-emerald-200",
          )}
          aria-label={isListening ? "Stop voice input" : "Start voice input"}
        >
          <Mic className={cn("h-4 w-4", isListening && "animate-pulse")} />
        </Button>
        <input
          value={value}
          onChange={(event) => onChange(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === "Enter") {
              event.preventDefault();
              onSubmit();
            }
          }}
          placeholder="Describe what you’re feeling in your own words"
          className="h-12 flex-1 bg-transparent px-2 text-base text-white outline-none placeholder:text-slate-400"
        />
        <Button
          type="button"
          onClick={onSubmit}
          disabled={isBusy || !value.trim()}
          className="gap-2 rounded-full px-5"
        >
          {isBusy ? <Loader2 className="h-4 w-4 animate-spin" /> : <SendHorizontal className="h-4 w-4" />}
          Continue
        </Button>
      </div>
    </div>
  );
}
