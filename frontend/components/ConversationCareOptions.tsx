"use client";

import { useEffect, useState } from "react";
import { ArrowUpRight, CheckCircle2, ChevronDown, ChevronUp, Clock3, CreditCard, Loader2, MapPin, Phone, ShieldCheck, X } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { callHospital, summarizeAppointmentReason } from "@/lib/api";
import { loadUserProfile } from "@/lib/session-store";
import type { AnalyzeResponse, AppointmentCallResponse, AppointmentCallStage, AppointmentTimeSlot, ChatMessage, HospitalLocation } from "@shared/types";

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
  chatHistory: ChatMessage[];
  defaultShowCosts?: boolean;
};

function optionForProvider(analysis: AnalyzeResponse, provider: string) {
  return analysis.cost_options.find((option) => option.provider === provider) ?? null;
}

function emptySlots(): AppointmentTimeSlot[] {
  return [
    { date: "", time: "" },
    { date: "", time: "" },
    { date: "", time: "" },
  ];
}

export function ConversationCareOptions({ analysis, copy, chatHistory, defaultShowCosts = false }: ConversationCareOptionsProps) {
  const PAGE_SIZE = 3;
  const [showCosts, setShowCosts] = useState(defaultShowCosts);
  const [callStageByHospital, setCallStageByHospital] = useState<Record<string, AppointmentCallStage>>({});
  const [callResults, setCallResults] = useState<Record<string, AppointmentCallResponse>>({});
  const [selectedHospital, setSelectedHospital] = useState<HospitalLocation | null>(null);
  const [timeSlots, setTimeSlots] = useState<AppointmentTimeSlot[]>(() => emptySlots());
  const [modalError, setModalError] = useState("");
  const [page, setPage] = useState(0);
  const hospitals = analysis.navigation.hospitals;
  const totalPages = Math.max(1, Math.ceil(hospitals.length / PAGE_SIZE));
  const pageStart = page * PAGE_SIZE;
  const visibleHospitals = hospitals.slice(pageStart, pageStart + PAGE_SIZE);
  const primaryHospital = visibleHospitals[0] ?? hospitals[0];
  const query = encodeURIComponent(primaryHospital ? primaryHospital.address : analysis.navigation.origin);

  useEffect(() => {
    setShowCosts(defaultShowCosts);
  }, [defaultShowCosts]);

  useEffect(() => {
    setPage(0);
  }, [analysis.request_id]);

  function openScheduleModal(hospital: HospitalLocation) {
    setSelectedHospital(hospital);
    setTimeSlots(emptySlots());
    setModalError("");
  }

  function closeScheduleModal() {
    setSelectedHospital(null);
    setTimeSlots(emptySlots());
    setModalError("");
  }

  async function handleCallHospital(hospital: HospitalLocation, slots: AppointmentTimeSlot[]) {
    const hospitalKey = `${hospital.name}-${hospital.address}`;
    const profile = loadUserProfile();
    const serializedHistory = chatHistory.map((message) => `${message.role}: ${message.content}`).join("\n");
    setCallStageByHospital((current) => ({ ...current, [hospitalKey]: "preparing" }));
    try {
      const { summary } = await summarizeAppointmentReason(serializedHistory);
      setCallStageByHospital((current) => ({ ...current, [hospitalKey]: "calling" }));
      const result = await callHospital({
        patient_name: profile.name || "User",
        reason_for_visit: summary,
        location: analysis.navigation.origin,
        time_slots: slots,
        hospital: {
          name: hospital.name,
          address: hospital.address,
          lat: hospital.lat,
          lng: hospital.lng,
          phone: hospital.phone,
          open_now: hospital.open_now,
          google_maps_uri: hospital.google_maps_uri ?? null,
        },
      });
      setCallResults((current) => ({ ...current, [hospitalKey]: result }));
    } catch {
      setCallResults((current) => ({
        ...current,
        [hospitalKey]: {
          status: "failed",
          call_id: "",
          appointment: null,
          slots_tried: [],
          transcript: "",
          recording_url: "",
          error: "Could not schedule appointment. Please try again.",
        },
      }));
    } finally {
      setCallStageByHospital((current) => {
        const next = { ...current };
        delete next[hospitalKey];
        return next;
      });
    }
  }

  async function confirmSchedule() {
    if (!selectedHospital) {
      return;
    }

    const normalizedSlots = timeSlots
      .map((slot) => ({ date: slot.date.trim(), time: slot.time.trim() }))
      .filter((slot) => slot.date && slot.time);

    if (normalizedSlots.length === 0) {
      setModalError("Please fill in at least the first preferred time slot.");
      return;
    }

    if (!timeSlots[0].date.trim() || !timeSlots[0].time.trim()) {
      setModalError("The first preferred time slot is required.");
      return;
    }

    const hospital = selectedHospital;
    closeScheduleModal();
    await handleCallHospital(hospital, normalizedSlots);
  }

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
        {visibleHospitals.map((hospital, index) => {
          const absoluteIndex = pageStart + index;
          const costOption = optionForProvider(analysis, hospital.name);
          const hospitalKey = `${hospital.name}-${hospital.address}`;
          const callResult = callResults[hospitalKey];
          const callStage = callStageByHospital[hospitalKey] ?? "idle";
          const isBusy = callStage === "preparing" || callStage === "calling";
          return (
            <div key={hospitalKey} className="rounded-[28px] border border-slate-200 bg-white p-5 shadow-[0_16px_40px_rgba(148,163,184,0.10)]">
              <div className="flex flex-col gap-4">
                <div className="flex flex-wrap items-center gap-3">
                  <h4 className="text-lg font-semibold text-slate-950">{hospital.name}</h4>
                  {absoluteIndex === 0 ? <Badge variant="safe">Recommended</Badge> : null}
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
                  <Button variant="secondary" onClick={() => openScheduleModal(hospital)} disabled={isBusy}>
                    {isBusy ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Phone className="mr-2 h-4 w-4" />}
                    {callStage === "preparing" ? "Preparing call..." : callStage === "calling" ? "Calling hospital..." : "Schedule"}
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

                {callResult?.status === "confirmed" && callResult.appointment ? (
                  <div className="rounded-[24px] border border-emerald-200 bg-emerald-50 p-4 text-sm text-emerald-800">
                    <p className="flex items-center gap-2 font-medium">
                      <CheckCircle2 className="h-4 w-4" />
                      Appointment confirmed
                    </p>
                    <div className="mt-3 space-y-1">
                      <p>Date: {callResult.appointment.date ?? "Not provided"}</p>
                      <p>Time: {callResult.appointment.time ?? "Not provided"}</p>
                      <p>Doctor: {callResult.appointment.doctor ?? "Not provided"}</p>
                      <p>Location: {callResult.appointment.location ?? "Not provided"}</p>
                      <p>Instructions: {callResult.appointment.instructions ?? "Not provided"}</p>
                    </div>
                  </div>
                ) : null}

                {callResult?.status === "failed" ? (
                  <div className="rounded-[24px] border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700">
                    Could not schedule appointment. Please try again.
                  </div>
                ) : null}

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

      {totalPages > 1 ? (
        <div className="flex flex-wrap items-center justify-between gap-3 rounded-[24px] border border-slate-200 bg-white px-4 py-3 text-sm text-slate-600 shadow-[0_16px_40px_rgba(148,163,184,0.08)]">
          <span>
            Showing options {pageStart + 1}-{Math.min(pageStart + PAGE_SIZE, hospitals.length)} of {hospitals.length}
          </span>
          <div className="flex gap-3">
            <Button variant="secondary" onClick={() => setPage((current) => Math.max(0, current - 1))} disabled={page === 0}>
              Previous
            </Button>
            <Button variant="secondary" onClick={() => setPage((current) => Math.min(totalPages - 1, current + 1))} disabled={page >= totalPages - 1}>
              More options
            </Button>
          </div>
        </div>
      ) : null}

      {selectedHospital ? (
        <div className="fixed inset-0 z-[80] flex items-center justify-center bg-slate-950/45 px-4">
          <div className="w-full max-w-2xl rounded-[32px] border border-slate-200 bg-white p-6 shadow-[0_40px_120px_rgba(15,23,42,0.28)]">
            <div className="flex items-start justify-between gap-4">
              <div>
                <h3 className="text-2xl font-semibold text-slate-950">When would you like your appointment?</h3>
                <p className="mt-2 text-sm leading-6 text-slate-600">Enter up to three preferred time slots for {selectedHospital.name}.</p>
              </div>
              <button
                type="button"
                onClick={closeScheduleModal}
                className="inline-flex h-10 w-10 items-center justify-center rounded-full border border-slate-200 text-slate-500 hover:text-slate-950"
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            <div className="mt-6 space-y-4">
              {timeSlots.map((slot, index) => (
                <div key={`slot-${index}`} className="grid gap-4 rounded-[24px] border border-slate-200 bg-slate-50 p-4 sm:grid-cols-2">
                  <label className="block">
                    <span className="mb-2 block text-xs uppercase tracking-[0.16em] text-slate-500">Date {index === 0 ? "(Required)" : "(Optional)"}</span>
                    <input
                      value={slot.date}
                      onChange={(event) =>
                        setTimeSlots((current) => current.map((item, itemIndex) => itemIndex === index ? { ...item, date: event.target.value } : item))
                      }
                      type="date"
                      className="h-12 w-full rounded-2xl border border-slate-200 bg-white px-4 text-sm text-slate-900 outline-none"
                    />
                  </label>
                  <label className="block">
                    <span className="mb-2 block text-xs uppercase tracking-[0.16em] text-slate-500">Time {index === 0 ? "(Required)" : "(Optional)"}</span>
                    <input
                      value={slot.time}
                      onChange={(event) =>
                        setTimeSlots((current) => current.map((item, itemIndex) => itemIndex === index ? { ...item, time: event.target.value } : item))
                      }
                      type="time"
                      className="h-12 w-full rounded-2xl border border-slate-200 bg-white px-4 text-sm text-slate-900 outline-none"
                    />
                  </label>
                </div>
              ))}
            </div>

            {modalError ? <p className="mt-4 text-sm text-rose-600">{modalError}</p> : null}

            <div className="mt-6 flex flex-col-reverse gap-3 sm:flex-row sm:justify-end">
              <Button variant="secondary" onClick={closeScheduleModal}>Cancel</Button>
              <Button onClick={() => void confirmSchedule()}>Call Now</Button>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}
