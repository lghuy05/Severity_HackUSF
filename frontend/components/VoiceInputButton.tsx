"use client";

type VoiceInputButtonProps = {
  isListening: boolean;
  onToggle: () => void;
};

export function VoiceInputButton({ isListening, onToggle }: VoiceInputButtonProps) {
  return (
    <button
      type="button"
      onClick={onToggle}
      className={[
        "inline-flex items-center justify-center rounded-full px-5 py-3 text-sm font-semibold transition",
        isListening ? "bg-alert text-white" : "bg-aqua text-ink",
      ].join(" ")}
    >
      {isListening ? "Stop Recording" : "Start Voice Input"}
    </button>
  );
}
