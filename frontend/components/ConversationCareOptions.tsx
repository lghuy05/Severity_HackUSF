"use client";

import { useState } from "react";
import { ArrowUpRight, ChevronDown, ChevronUp, Clock3, CreditCard, MapPin, Phone, ShieldCheck } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import type { AnalyzeResponse } from "@shared/types";

type ConversationCareOptionsProps = {
  analysis: AnalyzeResponse;
  copy: {
    careOptionsEyebrow: string;
    careOptionsTitle: string;
    careOptionsDescription: string;
    compareCosts: string;
    hideCosts: string;
    costRange: string;
    waitTime: string;
    coverage: string;
    call: string;
    directions: string;
    compare: string;
    openNow: string;
    hoursUnavailable: string;
    estimatedCostsReady: string;
    noCosts: string;
  };
  defaultShowCosts?: boolean;
};

function optionForProvider(analysis: AnalyzeResponse, provider: string) {
  return analysis.cost_options.find((option) => option.provider === provider) ?? null;
}

export function ConversationCareOptions({ analysis, copy, defaultShowCosts = false }: ConversationCareOptionsProps) {
  const [showCosts, setShowCosts] = useState(defaultShowCosts);
  const hospitals = analysis.navigation.hospitals.slice(0, 3);
  const primaryHospital = hospitals[0];
  const query = encodeURIComponent(primaryHospital ? primaryHospital.address : analysis.navigation.origin);

  if (!hospitals.length) {
    return null;
  }

  return (
    <div className="space-y-5">
      <div>
        <p className="text-xs uppercase tracking-[0.24em] text-slate-400">{copy.careOptionsEyebrow}</p>
        <h3 className="mt-2 text-2xl font-semibold text-slate-950">{copy.careOptionsTitle}</h3>
        <p className="mt-2 text-sm leading-7 text-slate-600">{copy.careOptionsDescription}</p>
      </div>

      <div className="overflow-hidden rounded-[28px] border border-slate-200 bg-white shadow-[0_16px_40px_rgba(148,163,184,0.10)]">
        <iframe
          title="Care map"
          src={`https://www.google.com/maps?q=${query}&z=12&output=embed`}
          className="h-[240px] w-full border-0"
          loading="lazy"
          referrerPolicy="no-referrer-when-downgrade"
        />
      </div>

      <div className="space-y-4">
        {hospitals.map((hospital, index) => {
          const costOption = optionForProvider(analysis, hospital.name);
          return (
            <div key={`${hospital.name}-${hospital.address}`} className="rounded-[28px] border border-slate-200 bg-white p-5 shadow-[0_16px_40px_rgba(148,163,184,0.10)]">
              <div className="flex flex-col gap-4">
                <div className="flex flex-wrap items-center gap-3">
                  <h4 className="text-lg font-semibold text-slate-950">{hospital.name}</h4>
                  {index === 0 ? <Badge variant="safe">Recommended</Badge> : null}
                  <Badge>{costOption?.care_type ?? "Hospital care"}</Badge>
                </div>

                <div className="flex flex-wrap items-center gap-4 text-sm text-slate-500">
                  <span className="inline-flex items-center gap-2">
                    <MapPin className="h-4 w-4 text-sky-500" />
                    {hospital.address}
                  </span>
                  <span className="inline-flex items-center gap-2">
                    <Phone className="h-4 w-4 text-slate-400" />
                    {hospital.phone}
                  </span>
                  <span className="inline-flex items-center gap-2">
                    <ShieldCheck className="h-4 w-4 text-emerald-500" />
                    {hospital.open_now ? copy.openNow : copy.hoursUnavailable}
                  </span>
                </div>

                <div className="grid gap-3 sm:grid-cols-3">
                  <Button asChild variant="secondary">
                    <a href={`tel:${hospital.phone}`}>{copy.call}</a>
                  </Button>
                  <Button asChild variant="secondary">
                    <a
                      href={
                        hospital.google_maps_uri ??
                        `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(hospital.address)}`
                      }
                      target="_blank"
                      rel="noreferrer"
                    >
                      {copy.directions}
                      <ArrowUpRight className="ml-2 h-4 w-4" />
                    </a>
                  </Button>
                  <Button variant="secondary" onClick={() => setShowCosts((current) => !current)}>
                    {showCosts ? copy.hideCosts : copy.compare}
                    {showCosts ? <ChevronUp className="ml-2 h-4 w-4" /> : <ChevronDown className="ml-2 h-4 w-4" />}
                  </Button>
                </div>

                {showCosts ? (
                  <div className="rounded-[24px] border border-slate-200 bg-slate-50/80 p-4">
                    {costOption ? (
                      <div className="space-y-3 text-sm">
                        <div className="font-medium text-slate-950">{copy.estimatedCostsReady}</div>
                        <div className="flex items-center justify-between gap-3">
                          <span className="inline-flex items-center gap-2 text-slate-500">
                            <CreditCard className="h-4 w-4 text-sky-500" />
                            {copy.costRange}
                          </span>
                          <span className="font-medium text-slate-950">{costOption.estimated_cost}</span>
                        </div>
                        <div className="flex items-center justify-between gap-3">
                          <span className="inline-flex items-center gap-2 text-slate-500">
                            <Clock3 className="h-4 w-4 text-violet-500" />
                            {copy.waitTime}
                          </span>
                          <span className="font-medium text-slate-950">{costOption.estimated_wait ?? "Unknown"}</span>
                        </div>
                        <div className="flex items-center justify-between gap-3">
                          <span className="text-slate-500">{copy.coverage}</span>
                          <span className="text-right text-slate-700">{costOption.coverage_summary ?? "Coverage varies"}</span>
                        </div>
                      </div>
                    ) : (
                      <p className="text-sm text-slate-600">{copy.noCosts}</p>
                    )}
                  </div>
                ) : null}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
