"use client";

import type { HospitalLocation } from "../../shared/types";

type HospitalListProps = {
  hospitals: HospitalLocation[];
};

export function HospitalList({ hospitals }: HospitalListProps) {
  return (
    <div className="space-y-3">
      {hospitals.map((hospital, index) => (
        <article
          key={`${hospital.name}-${hospital.address}`}
          className="animate-fade-in rounded-[24px] border border-white/10 bg-white/6 p-4 backdrop-blur-xl"
          style={{ animationDelay: `${index * 120}ms` }}
        >
          <p className="text-base font-semibold text-white">{hospital.name}</p>
          <p className="mt-1 text-sm text-slate-300">{hospital.address}</p>
          <p className="mt-2 text-sm text-slate-400">{hospital.phone}</p>
        </article>
      ))}
    </div>
  );
}
