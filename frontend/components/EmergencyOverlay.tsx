import { AlertTriangle, PhoneCall, X } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";

type EmergencyOverlayProps = {
  open: boolean;
  instructions: string[];
  onClose?: () => void;
};

export function EmergencyOverlay({ open, instructions, onClose }: EmergencyOverlayProps) {
  if (!open) {
    return null;
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-[rgba(7,9,15,0.72)] px-4 backdrop-blur-xl">
      <Card className="w-full max-w-2xl border-rose-400/[0.30] bg-[linear-gradient(180deg,rgba(80,18,31,0.94),rgba(26,8,14,0.98))] p-8 shadow-[0_30px_120px_rgba(127,29,29,0.45)]">
        {onClose ? (
          <button
            type="button"
            onClick={onClose}
            className="absolute right-4 top-4 inline-flex h-10 w-10 items-center justify-center rounded-full border border-white/10 bg-white/[0.06] text-white transition hover:bg-white/[0.12]"
            aria-label="Close emergency details"
          >
            <X className="h-4 w-4" />
          </button>
        ) : null}
        <div className="flex items-start gap-4">
          <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-rose-500/18 text-rose-200">
            <AlertTriangle className="h-7 w-7" />
          </div>
          <div className="flex-1">
            <p className="text-xs uppercase tracking-[0.28em] text-rose-200/70">Emergency detected</p>
            <h2 className="mt-2 text-3xl font-semibold text-white">Seek immediate emergency care</h2>
            <p className="mt-3 max-w-xl text-sm leading-7 text-rose-100/82">
              Symptoms suggest a potentially urgent condition. Call emergency services now and do not drive yourself if you
              feel faint, short of breath, or unsafe.
            </p>
          </div>
        </div>

        <div className="mt-6 space-y-3 rounded-[24px] border border-white/10 bg-black/[0.18] p-5">
          {instructions.map((instruction) => (
            <div key={instruction} className="text-sm leading-7 text-rose-50/92">
              {instruction}
            </div>
          ))}
        </div>

        <div className="mt-6 flex flex-col gap-3 sm:flex-row">
          <Button asChild variant="emergency" className="flex-1 gap-2">
            <a href="tel:911">
              <PhoneCall className="h-4 w-4" />
              Call 911
            </a>
          </Button>
          <Button asChild variant="secondary" className="flex-1">
            <a href="https://www.google.com/maps/search/emergency+room" target="_blank" rel="noreferrer">
              Find nearest ER
            </a>
          </Button>
        </div>
      </Card>
    </div>
  );
}
