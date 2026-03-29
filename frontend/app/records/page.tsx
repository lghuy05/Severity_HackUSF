"use client";

import { useEffect, useState } from "react";
import type { MouseEvent } from "react";
import Link from "next/link";
import { BookText, CalendarDays, ChevronDown, ChevronUp, Loader2, Sparkles, Trash2 } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { deleteVisitNote, listVisitNotes } from "@/lib/api";
import { getAppCopy } from "@/lib/app-copy";
import { useUiLanguage } from "@/lib/use-ui-language";
import type { VisitSavedNote } from "@shared/types";

function formatDate(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return new Intl.DateTimeFormat(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(date);
}

export default function RecordsPage() {
  const language = useUiLanguage();
  const copy = getAppCopy(language).records;
  const [notes, setNotes] = useState<VisitSavedNote[]>([]);
  const [expandedNoteId, setExpandedNoteId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    async function loadNotes() {
      try {
        const nextNotes = await listVisitNotes();
        setNotes(nextNotes);
        setExpandedNoteId(null);
        setError("");
      } catch {
        setError("Saved notes could not be loaded.");
      } finally {
        setIsLoading(false);
      }
    }

    void loadNotes();
  }, []);

  async function handleDelete(noteId: string) {
    setDeletingId(noteId);
    setError("");
    try {
      await deleteVisitNote(noteId);
      setNotes((current) => current.filter((note) => note.id !== noteId));
      setExpandedNoteId((current) => (current === noteId ? null : current));
    } catch {
      setError("Saved note could not be deleted.");
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
        ) : notes.length === 0 ? (
          <Card className="mt-10">
            <CardHeader className="border-b border-slate-200 pb-4">
              <CardTitle className="flex items-center gap-2">
                <BookText className="h-5 w-5 text-sky-500" />
                {copy.noNotesTitle}
              </CardTitle>
              <CardDescription className="mt-2">{copy.noNotesDescription}</CardDescription>
            </CardHeader>
            <CardContent className="flex min-h-[220px] flex-col items-center justify-center gap-4 text-center">
              <div className="flex h-16 w-16 items-center justify-center rounded-[22px] border border-slate-200 bg-slate-50">
                <Sparkles className="h-7 w-7 text-sky-500" />
              </div>
              <div>
                <p className="text-lg font-medium text-slate-900">{copy.nothingSaved}</p>
                <p className="mt-2 max-w-md text-sm leading-7 text-slate-500">
                  {copy.nothingSavedDescription}
                </p>
              </div>
              <Link href="/visit-assistant" className="inline-flex rounded-full bg-slate-950 px-5 py-3 text-sm font-medium text-white">
                {copy.openVisitAssistant}
              </Link>
            </CardContent>
          </Card>
        ) : (
          <div className="mt-10 space-y-4">
            {notes.map((note) => {
              const expanded = expandedNoteId === note.id;
              return (
                <Card key={note.id} className="overflow-hidden">
                  <button
                    type="button"
                    onClick={() => setExpandedNoteId((current) => current === note.id ? null : note.id)}
                    className="flex w-full items-center justify-between gap-4 px-6 py-5 text-left"
                  >
                    <div className="min-w-0">
                      <p className="text-lg font-semibold text-slate-950">{note.title}</p>
                      <div className="mt-2 flex flex-wrap items-center gap-3 text-sm text-slate-500">
                        <span className="inline-flex items-center gap-2">
                          <CalendarDays className="h-4 w-4" />
                          {formatDate(note.created_at)}
                        </span>
                        <span className="capitalize">{copy.severity}: {note.structured_note.severity}</span>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <Button
                        variant="secondary"
                        size="icon"
                        onClick={(event: MouseEvent<HTMLButtonElement>) => {
                          event.stopPropagation();
                          void handleDelete(note.id);
                        }}
                        disabled={deletingId === note.id}
                        aria-label="Delete note"
                      >
                        {deletingId === note.id ? <Loader2 className="h-4 w-4 animate-spin" /> : <Trash2 className="h-4 w-4" />}
                      </Button>
                      <span className="inline-flex items-center gap-2 rounded-full border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-600">
                        {expanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                        {expanded ? copy.collapse : copy.expand}
                      </span>
                    </div>
                  </button>

                  {expanded ? (
                    <CardContent className="border-t border-slate-200 bg-slate-50/70 p-6">
                      <div className="space-y-5">
                        <div>
                          <p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-400">AI summary</p>
                          <p className="mt-3 text-sm leading-7 text-slate-700">{note.summary}</p>
                        </div>
                        <div>
                          <p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-400">Clinical summary</p>
                          <p className="mt-3 text-sm leading-7 text-slate-700">{note.structured_note.summary}</p>
                        </div>
                        <div>
                          <p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-400">Timeline</p>
                          <p className="mt-3 text-sm leading-7 text-slate-700">{note.structured_note.timeline}</p>
                        </div>
                        <div>
                          <p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-400">Symptoms</p>
                          <div className="mt-3 flex flex-wrap gap-2">
                            {note.structured_note.symptoms.length > 0 ? note.structured_note.symptoms.map((symptom) => (
                              <span key={symptom} className="rounded-full border border-slate-200 bg-white px-3 py-1 text-xs text-slate-700">
                                {symptom}
                              </span>
                            )) : <span className="text-sm text-slate-500">No symptoms recorded.</span>}
                          </div>
                        </div>
                        <div>
                          <p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-400">Action items</p>
                          <div className="mt-3 space-y-2">
                            {note.structured_note.action_items.length > 0 ? note.structured_note.action_items.map((item) => (
                              <div key={item} className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-700">
                                {item}
                              </div>
                            )) : (
                              <div className="rounded-2xl border border-dashed border-slate-200 px-4 py-3 text-sm text-slate-500">
                                No action items recorded.
                              </div>
                            )}
                          </div>
                        </div>
                        <div>
                          <p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-400">Transcript</p>
                          <p className="mt-3 whitespace-pre-wrap text-sm leading-7 text-slate-600">{note.transcript}</p>
                        </div>
                      </div>
                    </CardContent>
                  ) : null}
                </Card>
              );
            })}
          </div>
        )}

      </div>
    </main>
  );
}
