"use client";

import { useEffect, useState } from "react";
import { CalendarDays, Loader2, MapPin, PlayCircle, Stethoscope, Trash2 } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { deleteAppointment, listAppointments } from "@/lib/api";
import { getAppCopy } from "@/lib/app-copy";
import { useUiLanguage } from "@/lib/use-ui-language";
import type { SavedAppointment } from "@shared/types";

function formatDateTime(date: string | null | undefined, time: string | null | undefined): string {
  return [date, time].filter(Boolean).join(" • ") || "Not provided";
}

function hasValue(value: string | null | undefined): boolean {
  return Boolean(value && value.trim());
}

export default function AppointmentsPage() {
  const language = useUiLanguage();
  const copy = getAppCopy(language).appointments;
  const [appointments, setAppointments] = useState<SavedAppointment[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    async function load() {
      try {
        const nextAppointments = await listAppointments();
        setAppointments(nextAppointments);
        setError("");
      } catch {
        setError("Appointments could not be loaded.");
      } finally {
        setIsLoading(false);
      }
    }

    void load();
  }, []);

  async function handleDelete(appointmentId: string) {
    setDeletingId(appointmentId);
    setError("");
    try {
      await deleteAppointment(appointmentId);
      setAppointments((current) => current.filter((appointment) => appointment.id !== appointmentId));
    } catch {
      setError("Appointment could not be deleted.");
    } finally {
      setDeletingId(null);
    }
  }

  return (
    <main className="app-shell-gradient min-h-screen">
      <div className="mx-auto max-w-5xl px-4 pb-16 pt-10 sm:px-6 lg:px-8">
        <Badge>{copy.badge}</Badge>
        <div className="mt-5 max-w-3xl">
          <h1 className="text-4xl font-semibold tracking-[-0.04em] text-slate-950 sm:text-5xl">{copy.title}</h1>
          <p className="mt-4 text-base leading-8 text-slate-600">{copy.description}</p>
        </div>

        {error ? (
          <div className="mt-8 rounded-[24px] border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
            {error}
          </div>
        ) : null}

        {isLoading ? (
          <Card className="mt-10">
            <CardContent className="flex min-h-[220px] items-center justify-center gap-3 text-slate-500">
              <Loader2 className="h-5 w-5 animate-spin" />
              {copy.loading}
            </CardContent>
          </Card>
        ) : appointments.length === 0 ? (
          <Card className="mt-10">
            <CardContent className="flex min-h-[220px] items-center justify-center text-center text-slate-500">
              {copy.empty}
            </CardContent>
          </Card>
        ) : (
          <div className="mt-10 space-y-4">
            {appointments.map((appointment) => (
              <Card key={appointment.id} className="overflow-hidden">
                <CardHeader className="border-b border-slate-200 pb-4">
                  <div className="flex flex-wrap items-center justify-between gap-3">
                    <div>
                      <CardTitle className="text-2xl tracking-[-0.03em]">{appointment.hospital || "Hospital"}</CardTitle>
                      <CardDescription className="mt-2 flex items-center gap-2">
                        <CalendarDays className="h-4 w-4" />
                        {formatDateTime(appointment.date, appointment.time)}
                      </CardDescription>
                    </div>
                    <div className="flex items-center gap-2">
                      <Badge variant="safe">{copy.confirmed}</Badge>
                      <Button
                        variant="secondary"
                        size="icon"
                        onClick={() => void handleDelete(appointment.id)}
                        disabled={deletingId === appointment.id}
                        aria-label="Delete appointment"
                      >
                        {deletingId === appointment.id ? <Loader2 className="h-4 w-4 animate-spin" /> : <Trash2 className="h-4 w-4" />}
                      </Button>
                    </div>
                  </div>
                </CardHeader>
                <CardContent className="space-y-4 pt-6">
                  {hasValue(appointment.doctor) || hasValue(appointment.location) ? (
                    <div className={`grid gap-4 ${hasValue(appointment.doctor) && hasValue(appointment.location) ? "sm:grid-cols-2" : "grid-cols-1"}`}>
                      {hasValue(appointment.doctor) ? (
                        <div className="rounded-[24px] border border-slate-200 bg-slate-50 p-4">
                          <p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-400">{copy.doctor}</p>
                          <p className="mt-2 text-sm text-slate-700">{appointment.doctor}</p>
                        </div>
                      ) : null}
                      {hasValue(appointment.location) ? (
                        <div className="rounded-[24px] border border-slate-200 bg-slate-50 p-4">
                          <p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-400">{copy.location}</p>
                          <p className="mt-2 flex items-center gap-2 text-sm text-slate-700">
                            <MapPin className="h-4 w-4 text-sky-500" />
                            {appointment.location}
                          </p>
                        </div>
                      ) : null}
                    </div>
                  ) : null}

                  <div className="rounded-[24px] border border-slate-200 bg-slate-50 p-4">
                    <p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-400">{copy.reasonForVisit}</p>
                    <p className="mt-2 flex items-start gap-2 text-sm leading-7 text-slate-700">
                      <Stethoscope className="mt-1 h-4 w-4 text-sky-500" />
                      <span>{appointment.reason_for_visit}</span>
                    </p>
                  </div>

                  {hasValue(appointment.instructions) ? (
                    <div className="rounded-[24px] border border-slate-200 bg-slate-50 p-4">
                      <p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-400">{copy.instructions}</p>
                      <p className="mt-2 text-sm leading-7 text-slate-700">{appointment.instructions}</p>
                    </div>
                  ) : null}

                  {appointment.recording_url ? (
                    <div className="flex justify-end">
                      <Button asChild variant="secondary">
                        <a href={appointment.recording_url} target="_blank" rel="noreferrer">
                          <PlayCircle className="mr-2 h-4 w-4" />
                          {copy.listenToRecording}
                        </a>
                      </Button>
                    </div>
                  ) : null}
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>
    </main>
  );
}
