"use client";

import { ArrowUpRight, Clock3, CreditCard, MapPin, Phone } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import type { AnalyzeResponse } from "@shared/types";

type CareOptionsBoardProps = {
  analysis: AnalyzeResponse;
};

function optionForProvider(analysis: AnalyzeResponse, provider: string) {
  return analysis.cost_options.find((option) => option.provider === provider) ?? null;
}

export function CareOptionsBoard({ analysis }: CareOptionsBoardProps) {
  const hospitals = analysis.navigation.hospitals;
  const primaryHospital = hospitals[0];
  const query = encodeURIComponent(primaryHospital ? primaryHospital.address : analysis.navigation.origin);

  return (
    <div className="space-y-8">
      <Card className="overflow-hidden p-0">
        <div className="border-b border-slate-200/80 px-8 py-7">
          <p className="text-xs uppercase tracking-[0.24em] text-slate-400">Care options</p>
          <h1 className="mt-2 text-4xl font-semibold tracking-[-0.04em] text-slate-950">Care near you</h1>
          <p className="mt-3 max-w-2xl text-base leading-7 text-slate-600">
            Based on your symptoms and location, these are the most relevant places to seek care next.
          </p>
        </div>

        <div className="relative">
          <iframe
            title="Care map"
            src={`https://www.google.com/maps?q=${query}&z=12&output=embed`}
            className="h-[420px] w-full border-0"
            loading="lazy"
            referrerPolicy="no-referrer-when-downgrade"
          />
          <div className="pointer-events-none absolute inset-x-0 top-0 h-24 bg-gradient-to-b from-white via-white/80 to-transparent" />
        </div>
      </Card>

      <div className="grid gap-5">
        {hospitals.map((hospital, index) => {
          const costOption = optionForProvider(analysis, hospital.name);
          return (
            <Card key={`${hospital.name}-${hospital.address}`} className="p-7">
              <div className="flex flex-col gap-6 lg:flex-row lg:items-center lg:justify-between">
                <div className="min-w-0 flex-1">
                  <div className="flex flex-wrap items-center gap-3">
                    <h2 className="text-2xl font-semibold text-slate-950">{hospital.name}</h2>
                    {index === 0 ? <Badge variant="safe">Recommended</Badge> : null}
                    <Badge>{costOption?.care_type ?? "Hospital care"}</Badge>
                  </div>
                  <div className="mt-3 flex flex-wrap items-center gap-4 text-sm text-slate-500">
                    <span className="inline-flex items-center gap-2">
                      <MapPin className="h-4 w-4 text-sky-500" />
                      {hospital.address}
                    </span>
                    <span className="inline-flex items-center gap-2">
                      <Phone className="h-4 w-4 text-slate-400" />
                      {hospital.phone}
                    </span>
                    <span>{hospital.open_now ? "Open now" : "Hours unavailable"}</span>
                  </div>
                  <p className="mt-4 max-w-3xl text-sm leading-7 text-slate-600">
                    {costOption?.notes ?? "This option is nearby and may be appropriate based on your current symptoms."}
                  </p>
                </div>

                <div className="grid gap-3 rounded-[28px] border border-slate-200 bg-slate-50/90 p-5 lg:min-w-[320px]">
                  <div className="flex items-center justify-between gap-3 text-sm">
                    <span className="inline-flex items-center gap-2 text-slate-500">
                      <CreditCard className="h-4 w-4 text-sky-500" />
                      Cost range
                    </span>
                    <span className="font-medium text-slate-950">{costOption?.estimated_cost ?? "Ask provider"}</span>
                  </div>
                  <div className="flex items-center justify-between gap-3 text-sm">
                    <span className="inline-flex items-center gap-2 text-slate-500">
                      <Clock3 className="h-4 w-4 text-violet-500" />
                      Wait time
                    </span>
                    <span className="font-medium text-slate-950">{costOption?.estimated_wait ?? "Unknown"}</span>
                  </div>
                  <div className="flex flex-col gap-3 pt-2 sm:flex-row">
                    <Button asChild className="flex-1">
                      <a href={hospital.google_maps_uri ?? `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(hospital.address)}`} target="_blank" rel="noreferrer">
                        Open map
                        <ArrowUpRight className="ml-2 h-4 w-4" />
                      </a>
                    </Button>
                    <Button asChild variant="secondary" className="flex-1">
                      <a href={`tel:${hospital.phone}`}>Call provider</a>
                    </Button>
                  </div>
                </div>
              </div>
            </Card>
          );
        })}
      </div>
    </div>
  );
}
