"use client";

type EmergencyBannerProps = {
  instructions: string[];
};

export function EmergencyBanner({ instructions }: EmergencyBannerProps) {
  return (
    <div className="rounded-[28px] border border-red-200 bg-red-50 p-5 shadow-panel">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.24em] text-alert">Emergency Mode</p>
          <h2 className="mt-1 text-2xl font-semibold text-alert">Seek urgent care now</h2>
        </div>
        <a
          href="tel:911"
          className="rounded-full bg-alert px-4 py-3 text-sm font-semibold text-white"
        >
          Call 911
        </a>
      </div>
      <div className="mt-4 space-y-2 text-sm text-red-900">
        {instructions.map((instruction) => (
          <p key={instruction}>{instruction}</p>
        ))}
      </div>
    </div>
  );
}
