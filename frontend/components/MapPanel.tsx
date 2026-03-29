import { ArrowUpRight, MapPinned, Phone } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import type { HospitalLocation } from "@shared/types";

type MapPanelProps = {
  hospitals: HospitalLocation[];
};

export function MapPanel({ hospitals }: MapPanelProps) {
  const primaryHospital = hospitals[0];
  const query = encodeURIComponent(primaryHospital ? primaryHospital.address : "hospital near me");

  return (
    <Card className="animate-slide-in-right overflow-hidden">
      <CardHeader className="border-b border-white/[0.08] pb-4">
        <div className="flex items-start justify-between gap-4">
          <div>
            <p className="text-xs uppercase tracking-[0.24em] text-slate-500">Navigation</p>
            <CardTitle className="mt-1 text-xl">Nearby care options</CardTitle>
            <CardDescription className="mt-2 max-w-md">
              These care options are based on your location and the current guidance from the backend.
            </CardDescription>
          </div>
          <Badge>Live routing</Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-4 pt-6">
        <div className="relative overflow-hidden rounded-[24px] border border-white/10 bg-[#0d1422]">
          <iframe
            title="Hospital map"
            src={`https://www.google.com/maps?q=${query}&z=13&output=embed`}
            className="h-[280px] w-full border-0 grayscale-[0.1] contrast-[1.05] saturate-[0.8]"
            loading="lazy"
            referrerPolicy="no-referrer-when-downgrade"
          />
          <div className="pointer-events-none absolute inset-x-0 top-0 h-24 bg-gradient-to-b from-[#0b0f14]/60 to-transparent" />
          <div className="pointer-events-none absolute bottom-4 left-4 right-4 flex flex-wrap gap-2">
            {hospitals.map((hospital) => (
              <div
                key={`${hospital.name}-${hospital.address}`}
                className="rounded-full border border-white/[0.12] bg-[#0f1828]/88 px-3 py-1.5 text-xs text-slate-100 backdrop-blur-xl"
              >
                <span className="mr-2 inline-flex h-2 w-2 rounded-full bg-emerald-400" />
                {hospital.name}
              </div>
            ))}
          </div>
        </div>

        <div className="space-y-3">
          {hospitals.map((hospital, index) => (
            <div
              key={`${hospital.name}-${hospital.phone}`}
              className="flex items-center justify-between gap-4 rounded-[22px] border border-white/10 bg-white/[0.04] px-4 py-4"
            >
              <div className="min-w-0">
                <div className="mb-2 flex items-center gap-2">
                  <MapPinned className="h-4 w-4 text-sky-300" />
                  <p className="truncate text-sm font-medium text-white">{hospital.name}</p>
                  {index === 0 ? <Badge variant="safe">Recommended</Badge> : null}
                </div>
                <p className="text-sm text-slate-300">{hospital.address}</p>
                <div className="mt-2 flex flex-wrap items-center gap-4 text-xs text-slate-400">
                  <span className="inline-flex items-center gap-1.5">
                    <Phone className="h-3.5 w-3.5" />
                    {hospital.phone}
                  </span>
                  <span>{hospital.open_now ? "Open now" : "Hours unavailable"}</span>
                </div>
              </div>
              <Button asChild variant="secondary" size="sm" className="shrink-0">
                <a
                  href={
                    hospital.google_maps_uri ??
                    `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(hospital.address)}`
                  }
                  target="_blank"
                  rel="noreferrer"
                >
                  Open
                  <ArrowUpRight className="h-3.5 w-3.5" />
                </a>
              </Button>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
