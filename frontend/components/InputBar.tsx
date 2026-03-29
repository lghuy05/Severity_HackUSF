"use client";

import { Loader2, Mic, SendHorizontal } from "lucide-react";

import { Button } from "@/components/ui/button";
import { LANGUAGE_OPTIONS } from "@/lib/i18n";
import { cn } from "@/lib/utils";

type InputBarProps = {
  value: string;
  onChange: (value: string) => void;
  language: string;
  onLanguageChange: (value: string) => void;
  onSubmit: () => void;
  onVoiceToggle: () => void;
  isListening?: boolean;
  voiceAvailable?: boolean;
  isBusy?: boolean;
  compact?: boolean;
  promptPlaceholder?: string;
  continueLabel?: string;
  voiceUnavailableTitle?: string;
  canSubmit?: boolean;
};

export function InputBar({
  value,
  onChange,
  language,
  onLanguageChange,
  onSubmit,
  onVoiceToggle,
  isListening = false,
  voiceAvailable = false,
  isBusy = false,
  compact = false,
  promptPlaceholder = "Describe what you're feeling in your own words",
  continueLabel = "Continue",
  voiceUnavailableTitle = "Voice input unavailable",
  canSubmit = true,
}: InputBarProps) {
  return (
    <div
      className={cn(
        "w-full rounded-[32px] border border-slate-200/80 bg-white/90 p-3 shadow-[0_28px_80px_rgba(148,163,184,0.16)] backdrop-blur-xl transition-all duration-300",
        compact ? "max-w-3xl" : "max-w-4xl",
        isListening && "scale-[1.01] border-sky-200 shadow-[0_32px_100px_rgba(56,189,248,0.20)]",
      )}
    >
      <div
        className={cn(
          "flex flex-col gap-3 rounded-[26px] bg-[linear-gradient(180deg,#ffffff_0%,#f8fbff_100%)] px-4 py-4 transition-all duration-300",
          isListening && "bg-[linear-gradient(180deg,#ffffff_0%,#eef8ff_100%)]",
        )}
      >
        <div className="flex items-center gap-2">
          <Button
            type="button"
            variant="secondary"
            size="icon"
            onClick={onVoiceToggle}
            disabled={!voiceAvailable}
            title={voiceAvailable ? undefined : voiceUnavailableTitle}
            className={cn(
              "shrink-0 rounded-full",
              isListening && "border-emerald-200 bg-emerald-50 text-emerald-700",
              !voiceAvailable && "cursor-not-allowed opacity-60",
            )}
            aria-label={isListening ? "Stop voice input" : "Start voice input"}
          >
            <Mic className={cn("h-4 w-4", isListening && "animate-pulse")} />
          </Button>
          <input
            value={value}
            onChange={(event) => onChange(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === "Enter" && !event.shiftKey) {
                event.preventDefault();
                onSubmit();
              }
            }}
            placeholder={promptPlaceholder}
            className="h-14 flex-1 bg-transparent px-2 text-base text-slate-950 outline-none placeholder:text-slate-400"
          />
          <Button
            type="button"
            onClick={onSubmit}
            disabled={isBusy || !value.trim() || !canSubmit}
            className="gap-2 rounded-full px-5"
          >
            {isBusy ? <Loader2 className="h-4 w-4 animate-spin" /> : <SendHorizontal className="h-4 w-4" />}
            {continueLabel}
          </Button>
        </div>
        <div className="rounded-[20px] border border-slate-200 bg-slate-50/70 px-4">
          <select
            value={language}
            onChange={(event) => onLanguageChange(event.target.value)}
            className="h-12 w-full bg-transparent text-sm text-slate-700 outline-none"
            aria-label="Select language"
          >
            {LANGUAGE_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </div>
      </div>
    </div>
  );
}
