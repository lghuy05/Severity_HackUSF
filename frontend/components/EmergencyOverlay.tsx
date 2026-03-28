"use client";

type EmergencyOverlayProps = {
  instructions: string[];
  visible: boolean;
};

export function EmergencyOverlay({ instructions, visible }: EmergencyOverlayProps) {
  return (
    <div
      className={[
        "pointer-events-none fixed inset-0 z-40 flex items-start justify-center px-4 pt-6 transition duration-500 md:px-8",
        visible ? "opacity-100" : "opacity-0",
      ].join(" ")}
    >
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_top,_rgba(239,68,68,0.18),transparent_38%),rgba(10,12,16,0.45)]" />
      <section className="pointer-events-auto relative w-full max-w-3xl rounded-[32px] border border-rose-400/25 bg-[#1C1012]/85 p-5 shadow-[0_24px_100px_rgba(127,29,29,0.35)] backdrop-blur-2xl md:p-6">
        <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
          <div>
            <p className="text-[11px] font-semibold uppercase tracking-[0.3em] text-rose-300">Emergency Mode</p>
            <h2 className="mt-2 text-2xl font-semibold text-white md:text-3xl">Seek immediate medical help</h2>
            <p className="mt-2 max-w-2xl text-sm leading-6 text-rose-100/85">
              The triage signal is high risk. Call emergency services now or go to the nearest emergency department.
            </p>
          </div>
          <a
            href="tel:911"
            className="inline-flex h-12 items-center justify-center rounded-full bg-rose-500 px-6 text-sm font-semibold text-white transition hover:shadow-[0_0_30px_rgba(244,63,94,0.4)]"
          >
            Call 911
          </a>
        </div>

        <div className="mt-5 grid gap-3 md:grid-cols-2">
          {instructions.map((instruction) => (
            <div key={instruction} className="rounded-[22px] border border-white/8 bg-white/5 p-4 text-sm leading-6 text-slate-100">
              {instruction}
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
