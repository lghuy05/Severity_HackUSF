"use client";

import type { HospitalLocation } from "../../shared/types";

type MapPanelProps = {
  hospitals: HospitalLocation[];
  location: string;
};

export function MapPanel({ hospitals, location }: MapPanelProps) {
  const apiKey = process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY;

  return (
    <div className="rounded-[28px] bg-white/90 p-5 shadow-panel backdrop-blur">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.24em] text-slate-500">Nearby Care</p>
          <h2 className="mt-1 text-xl font-semibold text-ink">Hospital Map</h2>
        </div>
        <span className="rounded-full bg-mist px-3 py-1 text-xs font-medium text-slate-600">{location}</span>
      </div>

      {apiKey ? (
        <iframe
          title="Google Map"
          className="mt-4 h-[280px] w-full rounded-3xl border-0"
          src={`https://www.google.com/maps/embed/v1/search?key=${apiKey}&q=${encodeURIComponent(location + " hospitals")}`}
          allowFullScreen
          loading="lazy"
        />
      ) : (
        <div className="mt-4 flex h-[280px] items-center justify-center rounded-3xl border border-dashed border-slate-300 bg-gradient-to-br from-slate-100 to-cyan-50 p-6 text-center text-sm text-slate-500">
          Add `NEXT_PUBLIC_GOOGLE_MAPS_API_KEY` to render the live Google Maps view. Mock hospital markers are listed below.
        </div>
      )}

      <div className="mt-4 space-y-3">
        {hospitals.map((hospital) => (
          <div key={hospital.name} className="rounded-2xl border border-slate-100 bg-slate-50 p-4">
            <p className="font-semibold text-ink">{hospital.name}</p>
            <p className="text-sm text-slate-500">{hospital.address}</p>
            <p className="text-sm text-slate-500">{hospital.phone}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
