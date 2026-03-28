"use client";

type MapViewProps = {
  location: string;
};

export function MapView({ location }: MapViewProps) {
  const apiKey = process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY;

  return apiKey ? (
    <iframe
      title="Nearby hospitals map"
      className="h-[320px] w-full rounded-[28px] border-0"
      src={`https://www.google.com/maps/embed/v1/search?key=${apiKey}&q=${encodeURIComponent(`${location} hospitals`)}`}
      allowFullScreen
      loading="lazy"
    />
  ) : (
    <div className="flex h-[320px] items-center justify-center rounded-[28px] border border-dashed border-white/12 bg-[radial-gradient(circle_at_top,_rgba(59,130,246,0.14),transparent_40%),#0E141C] px-8 text-center text-sm leading-6 text-slate-400">
      Add `NEXT_PUBLIC_GOOGLE_MAPS_API_KEY` to render the live Google Maps panel.
    </div>
  );
}
