"use client";

type VoiceButtonProps = {
  isListening: boolean;
  onToggle: () => void;
};

export function VoiceButton({ isListening, onToggle }: VoiceButtonProps) {
  return (
    <button
      type="button"
      onClick={onToggle}
      className={[
        "inline-flex h-14 w-14 items-center justify-center rounded-full border border-white/12 bg-white/8 text-white transition duration-300 hover:shadow-[0_0_30px_rgba(96,165,250,0.35)]",
        isListening ? "animate-agent-pulse border-rose-400/40 bg-rose-500/15 text-rose-100" : "",
      ].join(" ")}
      aria-label={isListening ? "Stop voice input" : "Start voice input"}
    >
      <span className="text-xl">{isListening ? "■" : "●"}</span>
    </button>
  );
}
