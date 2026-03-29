"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { Globe2, Languages, Loader2, Mic, PhoneCall, Sparkles, Square, Stethoscope, Volume2 } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { extractVisitNote, scheduleVisitAppointment, summarizeVisitConversation, translateVisitTurn } from "@/lib/api";
import { DEFAULT_PROFILE, loadUserProfile } from "@/lib/session-store";
import type { VisitAssistantUserProfile, VisitScheduleResponse, VisitStructuredNote, VisitTranslateTurnResponse } from "@shared/types";

declare global {
  interface Window {
    SpeechRecognition?: new () => SpeechRecognition;
    webkitSpeechRecognition?: new () => SpeechRecognition;
  }

  interface SpeechRecognition extends EventTarget {
    continuous: boolean;
    interimResults: boolean;
    lang: string;
    onresult: ((event: SpeechRecognitionEvent) => void) | null;
    onend: (() => void) | null;
    onerror: (() => void) | null;
    start(): void;
    stop(): void;
  }

  interface SpeechRecognitionEvent {
    resultIndex: number;
    results: ArrayLike<ArrayLike<{ transcript: string }>>;
  }
}

const EMPTY_NOTE: VisitStructuredNote = {
  summary: "",
  symptoms: [],
  severity: "unknown",
  timeline: "",
  action_items: [],
};

const LANGUAGE_OPTIONS = [
  { code: "en-US", label: "English" },
  { code: "es-ES", label: "Spanish" },
  { code: "fr-FR", label: "French" },
  { code: "pt-BR", label: "Portuguese" },
  { code: "vi-VN", label: "Vietnamese" },
  { code: "ht-HT", label: "Haitian Creole" },
  { code: "zh-CN", label: "Chinese" },
  { code: "ar-SA", label: "Arabic" },
];

type PageMode = "visit-summary" | "live-translator";
type TranslatorSide = "a" | "b";
type TranslatorTurn = VisitTranslateTurnResponse & { id: string; speaker: TranslatorSide };

function languageLabel(code: string): string {
  return LANGUAGE_OPTIONS.find((option) => option.code === code)?.label ?? code;
}

export default function VisitAssistantPage() {
  const recognitionRef = useRef<SpeechRecognition | null>(null);
  const shouldKeepRecordingRef = useRef(false);
  const activeRecorderRef = useRef<"visit" | TranslatorSide | null>(null);
  const pendingTranslateSideRef = useRef<TranslatorSide | null>(null);
  const translatorSourceARef = useRef("");
  const translatorSourceBRef = useRef("");
  const translatorLanguageARef = useRef("en-US");
  const translatorLanguageBRef = useRef("es-ES");
  const [mode, setMode] = useState<PageMode>("visit-summary");
  const [visitTranscript, setVisitTranscript] = useState("");
  const [visitInterimTranscript, setVisitInterimTranscript] = useState("");
  const [note, setNote] = useState<VisitStructuredNote | null>(null);
  const [conversationSummary, setConversationSummary] = useState("");
  const [scheduleResult, setScheduleResult] = useState<VisitScheduleResponse | null>(null);
  const [error, setError] = useState("");
  const [isSupported, setIsSupported] = useState(false);
  const [isVisitRecording, setIsVisitRecording] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [isScheduling, setIsScheduling] = useState(false);
  const [translatorSourceA, setTranslatorSourceA] = useState("");
  const [translatorInterimA, setTranslatorInterimA] = useState("");
  const [translatorSourceB, setTranslatorSourceB] = useState("");
  const [translatorInterimB, setTranslatorInterimB] = useState("");
  const [translatorLanguageA, setTranslatorLanguageA] = useState("en-US");
  const [translatorLanguageB, setTranslatorLanguageB] = useState("es-ES");
  const [translatorTurns, setTranslatorTurns] = useState<TranslatorTurn[]>([]);
  const [activeTranslatorSide, setActiveTranslatorSide] = useState<TranslatorSide | null>(null);
  const [isTranslating, setIsTranslating] = useState<TranslatorSide | null>(null);
  const [translatorSummary, setTranslatorSummary] = useState("");
  const [translatorNote, setTranslatorNote] = useState<VisitStructuredNote | null>(null);
  const [isSummarizingTranslator, setIsSummarizingTranslator] = useState(false);
  const [form, setForm] = useState<VisitAssistantUserProfile>({
    full_name: "",
    phone_number: "",
    language: DEFAULT_PROFILE.language,
    location: DEFAULT_PROFILE.location,
    age: DEFAULT_PROFILE.age,
    gender: DEFAULT_PROFILE.gender,
  });

  useEffect(() => {
    translatorLanguageARef.current = translatorLanguageA;
  }, [translatorLanguageA]);

  useEffect(() => {
    translatorLanguageBRef.current = translatorLanguageB;
  }, [translatorLanguageB]);

  useEffect(() => {
    translatorSourceARef.current = translatorSourceA;
  }, [translatorSourceA]);

  useEffect(() => {
    translatorSourceBRef.current = translatorSourceB;
  }, [translatorSourceB]);

  useEffect(() => {
    const savedProfile = loadUserProfile();
    setForm((current) => ({
      ...current,
      language: savedProfile.language || "en",
      location: savedProfile.location || "",
      age: savedProfile.age,
      gender: savedProfile.gender,
    }));

    const Recognition = window.SpeechRecognition ?? window.webkitSpeechRecognition;
    if (!Recognition) {
      setIsSupported(false);
      return;
    }

    const recognition = new Recognition();
    recognition.lang = "en-US";
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.onresult = (event) => {
      let finalizedChunk = "";
      let interimChunk = "";

      for (let index = event.resultIndex; index < event.results.length; index += 1) {
        const result = event.results[index] as ArrayLike<{ transcript: string }> & { isFinal?: boolean };
        const text = result[0]?.transcript?.trim() ?? "";
        if (!text) {
          continue;
        }
        if (result.isFinal) {
          finalizedChunk += `${text} `;
        } else {
          interimChunk += `${text} `;
        }
      }

      const activeRecorder = activeRecorderRef.current;
      if (activeRecorder === "visit") {
        if (finalizedChunk.trim()) {
          setVisitTranscript((current) => `${current} ${finalizedChunk}`.replace(/\s+/g, " ").trim());
        }
        setVisitInterimTranscript(interimChunk.trim());
        return;
      }

      if (activeRecorder === "a") {
        if (finalizedChunk.trim()) {
          setTranslatorSourceA((current) => {
            const next = `${current} ${finalizedChunk}`.replace(/\s+/g, " ").trim();
            translatorSourceARef.current = next;
            return next;
          });
        }
        setTranslatorInterimA(interimChunk.trim());
        return;
      }

      if (activeRecorder === "b") {
        if (finalizedChunk.trim()) {
          setTranslatorSourceB((current) => {
            const next = `${current} ${finalizedChunk}`.replace(/\s+/g, " ").trim();
            translatorSourceBRef.current = next;
            return next;
          });
        }
        setTranslatorInterimB(interimChunk.trim());
      }
    };
    recognition.onend = () => {
      const pendingTranslateSide = pendingTranslateSideRef.current;
      clearInterimForActiveRecorder();
      if (shouldKeepRecordingRef.current) {
        try {
          recognition.start();
          return;
        } catch {
          window.setTimeout(() => {
            if (!shouldKeepRecordingRef.current) {
              return;
            }
            try {
              recognition.start();
            } catch {
              stopActiveRecordingState();
              setError("Voice transcription stopped unexpectedly. You can keep typing the transcript manually.");
            }
          }, 250);
          return;
        }
      }
      stopActiveRecordingState();
      if (pendingTranslateSide) {
        pendingTranslateSideRef.current = null;
        window.setTimeout(() => {
          void handleTranslate(pendingTranslateSide);
        }, 0);
      }
    };
    recognition.onerror = () => {
      clearInterimForActiveRecorder();
      if (!shouldKeepRecordingRef.current) {
        stopActiveRecordingState();
        return;
      }
      window.setTimeout(() => {
        if (!shouldKeepRecordingRef.current) {
          return;
        }
        try {
          recognition.start();
        } catch {
          stopActiveRecordingState();
          setError("Voice transcription stopped unexpectedly. You can keep typing the transcript manually.");
        }
      }, 250);
    };
    recognitionRef.current = recognition;
    setIsSupported(true);

    return () => {
      shouldKeepRecordingRef.current = false;
      activeRecorderRef.current = null;
      pendingTranslateSideRef.current = null;
      clearAllInterim();
      recognition.stop();
    };
  }, []);

  const canGenerate = visitTranscript.trim().length > 0 && !isGenerating;
  const canSchedule = Boolean(note) && !isScheduling;
  const symptoms = note?.symptoms ?? EMPTY_NOTE.symptoms;
  const actionItems = note?.action_items ?? EMPTY_NOTE.action_items;

  const scheduleHint = useMemo(() => {
    if (!note) {
      return "Generate a structured note first.";
    }
    if (!form.phone_number.trim()) {
      return "Add a phone number to send the visit note into the scheduling flow.";
    }
    return "Ready to hand off to VAPI scheduling.";
  }, [form.phone_number, note]);

  function clearAllInterim() {
    setVisitInterimTranscript("");
    setTranslatorInterimA("");
    setTranslatorInterimB("");
  }

  function clearInterimForActiveRecorder() {
    const activeRecorder = activeRecorderRef.current;
    if (activeRecorder === "visit") {
      setVisitInterimTranscript("");
    } else if (activeRecorder === "a") {
      setTranslatorInterimA("");
    } else if (activeRecorder === "b") {
      setTranslatorInterimB("");
    }
  }

  function stopActiveRecordingState() {
    shouldKeepRecordingRef.current = false;
    if (activeRecorderRef.current === "visit") {
      setIsVisitRecording(false);
    } else if (activeRecorderRef.current === "a" || activeRecorderRef.current === "b") {
      setActiveTranslatorSide(null);
    }
    activeRecorderRef.current = null;
  }

  function startRecording(recorder: "visit" | TranslatorSide, lang: string) {
    setError("");
    if (!recognitionRef.current) {
      return;
    }

    if (activeRecorderRef.current) {
      shouldKeepRecordingRef.current = false;
      recognitionRef.current.stop();
    }

    clearAllInterim();
    recognitionRef.current.lang = lang;

    try {
      shouldKeepRecordingRef.current = true;
      activeRecorderRef.current = recorder;
      recognitionRef.current.start();
      if (recorder === "visit") {
        setIsVisitRecording(true);
        setActiveTranslatorSide(null);
      } else {
        setActiveTranslatorSide(recorder);
        setIsVisitRecording(false);
      }
    } catch {
      stopActiveRecordingState();
      setError("Voice transcription could not start. You can keep typing the transcript manually.");
    }
  }

  function stopRecording() {
    if (!recognitionRef.current) {
      return;
    }
    const recorder = activeRecorderRef.current;
    shouldKeepRecordingRef.current = false;
    if (recorder === "a" || recorder === "b") {
      pendingTranslateSideRef.current = recorder;
    }
    clearInterimForActiveRecorder();
    recognitionRef.current.stop();
  }

  async function handleGenerate() {
    if (!visitTranscript.trim()) {
      return;
    }

    setError("");
    setScheduleResult(null);
    setIsGenerating(true);
    try {
      const [noteResponse, summaryResponse] = await Promise.all([
        extractVisitNote(visitTranscript),
        summarizeVisitConversation(visitTranscript),
      ]);
      setNote(noteResponse.note);
      setConversationSummary(summaryResponse.summary);
    } catch {
      setError("Visit Assistant could not process the transcript.");
    } finally {
      setIsGenerating(false);
    }
  }

  async function handleSchedule() {
    if (!note) {
      return;
    }

    setError("");
    setIsScheduling(true);
    try {
      const response = await scheduleVisitAppointment(note, form);
      setScheduleResult(response);
    } catch {
      setError("Scheduling could not be completed.");
    } finally {
      setIsScheduling(false);
    }
  }

  function speakText(text: string, language: string) {
    if (typeof window === "undefined" || !("speechSynthesis" in window)) {
      return;
    }
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = language;
    window.speechSynthesis.cancel();
    window.speechSynthesis.speak(utterance);
  }

  function buildTranslatorTranscript(turns: TranslatorTurn[]): string {
    return turns
      .map((turn) =>
        turn.speaker === "a"
          ? `Speaker A said in ${languageLabel(turn.source_language)}: ${turn.source_text}\nTranslated for Speaker B in ${languageLabel(turn.target_language)}: ${turn.translated_text}`
          : `Speaker B said in ${languageLabel(turn.source_language)}: ${turn.source_text}\nTranslated for Speaker A in ${languageLabel(turn.target_language)}: ${turn.translated_text}`,
      )
      .join("\n\n");
  }

  async function handleTranslate(side: TranslatorSide) {
    const sourceText = (side === "a" ? translatorSourceARef.current : translatorSourceBRef.current).trim();
    const sourceLanguage = side === "a" ? translatorLanguageARef.current : translatorLanguageBRef.current;
    const targetLanguage = side === "a" ? translatorLanguageBRef.current : translatorLanguageARef.current;
    if (!sourceText) {
      return;
    }

    setError("");
    setIsTranslating(side);
    try {
      const response = await translateVisitTurn({
        text: sourceText,
        source_language: sourceLanguage,
        target_language: targetLanguage,
      });
      setTranslatorTurns((current) => [...current, { ...response, id: crypto.randomUUID(), speaker: side }]);
      speakText(response.translated_text, targetLanguage);
      if (side === "a") {
        translatorSourceARef.current = "";
        setTranslatorSourceA("");
        setTranslatorInterimA("");
      } else {
        translatorSourceBRef.current = "";
        setTranslatorSourceB("");
        setTranslatorInterimB("");
      }
    } catch {
      setError("Live translation could not be completed.");
    } finally {
      setIsTranslating(null);
    }
  }

  async function handleTranslatorSummary() {
    if (translatorTurns.length === 0) {
      return;
    }

    setError("");
    setIsSummarizingTranslator(true);
    try {
      const transcript = buildTranslatorTranscript(translatorTurns);
      const [noteResponse, summaryResponse] = await Promise.all([
        extractVisitNote(transcript),
        summarizeVisitConversation(transcript),
      ]);
      setTranslatorNote(noteResponse.note);
      setTranslatorSummary(summaryResponse.summary);
    } catch {
      setError("AI summary could not be generated for the translated conversation.");
    } finally {
      setIsSummarizingTranslator(false);
    }
  }

  const visitDisplayTranscript = [visitTranscript, visitInterimTranscript].filter(Boolean).join(" ").trim();
  return (
    <main className="mx-auto flex min-h-[calc(100vh-88px)] w-full max-w-6xl flex-col gap-8 px-4 py-8 sm:px-6 lg:px-8">
      <section className="flex flex-wrap items-center gap-3">
        <button
          type="button"
          onClick={() => setMode("visit-summary")}
          className={`inline-flex items-center gap-2 rounded-full px-4 py-2 text-sm font-medium transition ${mode === "visit-summary" ? "bg-slate-950 text-white" : "border border-slate-200 bg-white text-slate-600 hover:text-slate-950"}`}
        >
          <Stethoscope className="h-4 w-4" />
          Visit Summary
        </button>
        <button
          type="button"
          onClick={() => setMode("live-translator")}
          className={`inline-flex items-center gap-2 rounded-full px-4 py-2 text-sm font-medium transition ${mode === "live-translator" ? "bg-slate-950 text-white" : "border border-slate-200 bg-white text-slate-600 hover:text-slate-950"}`}
        >
          <Languages className="h-4 w-4" />
          Live Translator
        </button>
      </section>

      {error ? (
        <div className="rounded-[24px] border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
          {error}
        </div>
      ) : null}

      {mode === "visit-summary" ? (
        <>
          <section className="grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">
            <Card className="overflow-hidden border-slate-200/80 bg-white/90">
              <CardHeader className="gap-4 border-b border-slate-100 bg-[linear-gradient(180deg,rgba(255,255,255,0.95),rgba(248,250,252,0.78))]">
                <div className="inline-flex w-fit items-center gap-2 rounded-full border border-slate-200 bg-white px-3 py-1 text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
                  <Stethoscope className="h-3.5 w-3.5" />
                  Visit Assistant
                </div>
                <div className="space-y-2">
                  <CardTitle className="text-3xl font-semibold tracking-[-0.04em]">Transcript to visit summary, separate from the chat system.</CardTitle>
                  <CardDescription className="max-w-2xl text-sm leading-6 text-slate-600">
                    Record or paste a visit transcript, generate a structured note, and hand the result to the scheduling flow through `/visit/*` only.
                  </CardDescription>
                </div>
              </CardHeader>
              <CardContent className="space-y-6 p-6">
                <div className="flex flex-wrap items-center gap-3">
                  <Button type="button" size="lg" onClick={() => (isVisitRecording ? stopRecording() : startRecording("visit", "en-US"))} disabled={!isSupported} className="min-w-[200px]">
                    {isVisitRecording ? <Square className="mr-2 h-4 w-4" /> : <Mic className="mr-2 h-4 w-4" />}
                    {isVisitRecording ? "Stop recording" : "Record transcript"}
                  </Button>
                  <Button type="button" variant="secondary" size="lg" onClick={handleGenerate} disabled={!canGenerate}>
                    {isGenerating ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Sparkles className="mr-2 h-4 w-4" />}
                    Generate summary
                  </Button>
                  {!isSupported ? (
                    <span className="text-sm text-amber-600">Browser speech recognition is unavailable. Paste the transcript manually.</span>
                  ) : null}
                </div>

                <label className="block space-y-3">
                  <span className="text-sm font-medium text-slate-700">Transcript</span>
                  <textarea
                    value={visitDisplayTranscript}
                    onChange={(event) => {
                      setVisitTranscript(event.target.value);
                      setVisitInterimTranscript("");
                    }}
                    placeholder="Paste or record the visit transcript here."
                    className="min-h-64 w-full rounded-[28px] border border-slate-200 bg-slate-50 px-5 py-4 text-sm leading-6 text-slate-900 outline-none transition focus:border-slate-300 focus:bg-white focus:ring-4 focus:ring-sky-100"
                  />
                </label>
              </CardContent>
            </Card>

            <Card className="border-slate-200/80 bg-[linear-gradient(180deg,rgba(15,23,42,0.96),rgba(30,41,59,0.96))] text-white shadow-[0_40px_100px_rgba(15,23,42,0.26)]">
              <CardHeader>
                <CardTitle className="text-2xl tracking-[-0.03em]">Scheduling handoff</CardTitle>
                <CardDescription className="text-slate-300">
                  Send the extracted note plus patient details to the VAPI scheduling flow.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <label className="block space-y-2">
                  <span className="text-sm font-medium text-slate-200">Full name</span>
                  <input value={form.full_name} onChange={(event) => setForm((current) => ({ ...current, full_name: event.target.value }))} className="h-12 w-full rounded-2xl border border-slate-700 bg-slate-900/70 px-4 text-sm text-white outline-none transition focus:border-sky-400 focus:ring-4 focus:ring-sky-500/20" placeholder="Jane Doe" />
                </label>
                <label className="block space-y-2">
                  <span className="text-sm font-medium text-slate-200">Phone number</span>
                  <input value={form.phone_number} onChange={(event) => setForm((current) => ({ ...current, phone_number: event.target.value }))} className="h-12 w-full rounded-2xl border border-slate-700 bg-slate-900/70 px-4 text-sm text-white outline-none transition focus:border-sky-400 focus:ring-4 focus:ring-sky-500/20" placeholder="5551234567" />
                </label>
                <label className="block space-y-2">
                  <span className="text-sm font-medium text-slate-200">Location</span>
                  <input value={form.location} onChange={(event) => setForm((current) => ({ ...current, location: event.target.value }))} className="h-12 w-full rounded-2xl border border-slate-700 bg-slate-900/70 px-4 text-sm text-white outline-none transition focus:border-sky-400 focus:ring-4 focus:ring-sky-500/20" placeholder="Boston, MA" />
                </label>
                <div className="rounded-[24px] border border-slate-700 bg-white/5 px-4 py-3 text-sm text-slate-300">{scheduleHint}</div>
                <Button type="button" size="lg" onClick={handleSchedule} disabled={!canSchedule} className="w-full bg-white text-slate-950 hover:bg-slate-100">
                  {isScheduling ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <PhoneCall className="mr-2 h-4 w-4" />}
                  Schedule appointment
                </Button>
                {scheduleResult ? (
                  <div className="rounded-[24px] border border-emerald-400/25 bg-emerald-400/10 px-4 py-4 text-sm text-emerald-50">
                    <p className="font-medium">{scheduleResult.message}</p>
                    <p className="mt-1 text-emerald-100/80">
                      Status: {scheduleResult.status}
                      {scheduleResult.external_call_id ? ` • Call ID: ${scheduleResult.external_call_id}` : ""}
                    </p>
                  </div>
                ) : null}
              </CardContent>
            </Card>
          </section>

          <section className="grid gap-6 lg:grid-cols-[1.15fr_0.85fr]">
            <Card>
              <CardHeader>
                <CardTitle>Visit summary</CardTitle>
                <CardDescription>Human-readable summary generated from the transcript.</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="rounded-[28px] border border-slate-200 bg-slate-50 px-5 py-4 text-sm leading-7 text-slate-700">
                  {conversationSummary || "Generate a summary to populate this section."}
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Structured note</CardTitle>
                <CardDescription>HelloCare-style extraction adapted into a standalone FastAPI service.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-5">
                <div>
                  <p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-400">Severity</p>
                  <p className="mt-2 text-sm font-medium capitalize text-slate-900">{note?.severity ?? "unknown"}</p>
                </div>
                <div>
                  <p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-400">Clinical summary</p>
                  <p className="mt-2 text-sm leading-6 text-slate-700">{note?.summary || "No structured note generated yet."}</p>
                </div>
                <div>
                  <p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-400">Timeline</p>
                  <p className="mt-2 text-sm leading-6 text-slate-700">{note?.timeline || "No timeline extracted yet."}</p>
                </div>
              </CardContent>
            </Card>
          </section>

          <section className="grid gap-6 md:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle>Symptoms</CardTitle>
                <CardDescription>Short extracted findings suitable for downstream handoff later.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                {symptoms.length > 0 ? symptoms.map((symptom) => (
                  <div key={symptom} className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-700">
                    {symptom}
                  </div>
                )) : (
                  <div className="rounded-2xl border border-dashed border-slate-200 px-4 py-3 text-sm text-slate-500">
                    No symptoms extracted yet.
                  </div>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Action items</CardTitle>
                <CardDescription>Follow-ups, scheduling needs, and explicit next steps.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                {actionItems.length > 0 ? actionItems.map((item) => (
                  <div key={item} className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-700">
                    {item}
                  </div>
                )) : (
                  <div className="rounded-2xl border border-dashed border-slate-200 px-4 py-3 text-sm text-slate-500">
                    No action items extracted yet.
                  </div>
                )}
              </CardContent>
            </Card>
          </section>
        </>
      ) : (
        <>
          <section className="grid gap-6 lg:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2"><Globe2 className="h-5 w-5" /> Speaker A</CardTitle>
                <CardDescription>Speak in Language A. When you stop, the translated message will appear for Speaker B and play aloud.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <select value={translatorLanguageA} onChange={(event) => setTranslatorLanguageA(event.target.value)} className="h-12 w-full rounded-2xl border border-slate-200 bg-white px-4 text-sm text-slate-900 outline-none focus:border-slate-300 focus:ring-4 focus:ring-sky-100">
                  {LANGUAGE_OPTIONS.map((option) => <option key={option.code} value={option.code}>{option.label}</option>)}
                </select>
                <div className="flex gap-3">
                  <Button type="button" onClick={() => (activeTranslatorSide === "a" ? stopRecording() : startRecording("a", translatorLanguageA))} disabled={!isSupported} className="flex-1">
                    {activeTranslatorSide === "a" ? <Square className="mr-2 h-4 w-4" /> : <Mic className="mr-2 h-4 w-4" />}
                    {activeTranslatorSide === "a" ? "Stop" : "Speak A"}
                  </Button>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2"><Globe2 className="h-5 w-5" /> Speaker B</CardTitle>
                <CardDescription>Speak in Language B. When you stop, the translated message will appear for Speaker A and play aloud.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <select value={translatorLanguageB} onChange={(event) => setTranslatorLanguageB(event.target.value)} className="h-12 w-full rounded-2xl border border-slate-200 bg-white px-4 text-sm text-slate-900 outline-none focus:border-slate-300 focus:ring-4 focus:ring-sky-100">
                  {LANGUAGE_OPTIONS.map((option) => <option key={option.code} value={option.code}>{option.label}</option>)}
                </select>
                <div className="flex gap-3">
                  <Button type="button" onClick={() => (activeTranslatorSide === "b" ? stopRecording() : startRecording("b", translatorLanguageB))} disabled={!isSupported} className="flex-1">
                    {activeTranslatorSide === "b" ? <Square className="mr-2 h-4 w-4" /> : <Mic className="mr-2 h-4 w-4" />}
                    {activeTranslatorSide === "b" ? "Stop" : "Speak B"}
                  </Button>
                </div>
              </CardContent>
            </Card>
          </section>

          <section>
            <Card>
              <CardHeader>
                <CardTitle>Conversation feed</CardTitle>
                <CardDescription>Each spoken turn appears as a translated bubble for the other side. You can generate an AI summary from the accumulated conversation.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex justify-end">
                  <Button type="button" variant="secondary" onClick={handleTranslatorSummary} disabled={translatorTurns.length === 0 || isSummarizingTranslator}>
                    {isSummarizingTranslator ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Sparkles className="mr-2 h-4 w-4" />}
                    Generate AI summary
                  </Button>
                </div>
                {translatorTurns.length > 0 ? translatorTurns.map((turn) => (
                  <div key={turn.id} className={`flex ${turn.speaker === "a" ? "justify-end" : "justify-start"}`}>
                    <div className={`max-w-[80%] rounded-[28px] px-5 py-4 shadow-sm ${turn.speaker === "a" ? "bg-slate-950 text-white" : "bg-slate-100 text-slate-900"}`}>
                      <p className={`text-[11px] font-semibold uppercase tracking-[0.16em] ${turn.speaker === "a" ? "text-slate-300" : "text-slate-500"}`}>
                        {turn.speaker === "a" ? `For Speaker B • ${languageLabel(turn.target_language)}` : `For Speaker A • ${languageLabel(turn.target_language)}`}
                      </p>
                      <p className="mt-2 text-sm leading-6">{turn.translated_text}</p>
                      <div className="mt-3 flex items-center justify-between gap-3">
                        <p className={`text-xs ${turn.speaker === "a" ? "text-slate-400" : "text-slate-500"}`}>
                          Heard in {languageLabel(turn.source_language)}
                        </p>
                        <button
                          type="button"
                          onClick={() => speakText(turn.translated_text, turn.target_language)}
                          className={`inline-flex items-center gap-2 rounded-full px-3 py-2 text-xs font-medium ${turn.speaker === "a" ? "bg-white/10 text-white hover:bg-white/15" : "bg-white text-slate-700 hover:text-slate-950"}`}
                        >
                          <Volume2 className="h-3.5 w-3.5" />
                          Replay
                        </button>
                      </div>
                    </div>
                  </div>
                )) : (
                  <div className="rounded-[24px] border border-dashed border-slate-200 px-4 py-6 text-sm text-slate-500">
                    Start speaking on either side and stop manually. The translated turn will appear here as a chat bubble for the other person.
                  </div>
                )}
              </CardContent>
            </Card>
          </section>

          {(translatorSummary || translatorNote) ? (
            <section className="grid gap-6 lg:grid-cols-[1.15fr_0.85fr]">
              <Card>
                <CardHeader>
                  <CardTitle>AI summary</CardTitle>
                  <CardDescription>Generated from the translated conversation history.</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="rounded-[28px] border border-slate-200 bg-slate-50 px-5 py-4 text-sm leading-7 text-slate-700">
                    {translatorSummary || "No summary generated yet."}
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>AI note</CardTitle>
                  <CardDescription>Structured note-taking over the accumulated translated conversation.</CardDescription>
                </CardHeader>
                <CardContent className="space-y-5">
                  <div>
                    <p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-400">Clinical summary</p>
                    <p className="mt-2 text-sm leading-6 text-slate-700">{translatorNote?.summary || "No note generated yet."}</p>
                  </div>
                  <div>
                    <p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-400">Severity</p>
                    <p className="mt-2 text-sm font-medium capitalize text-slate-900">{translatorNote?.severity ?? "unknown"}</p>
                  </div>
                  <div>
                    <p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-400">Symptoms</p>
                    <div className="mt-2 flex flex-wrap gap-2">
                      {(translatorNote?.symptoms ?? []).length > 0 ? (translatorNote?.symptoms ?? []).map((symptom) => (
                        <span key={symptom} className="rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-xs text-slate-700">
                          {symptom}
                        </span>
                      )) : <span className="text-sm text-slate-500">No symptoms extracted.</span>}
                    </div>
                  </div>
                  <div>
                    <p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-400">Action items</p>
                    <div className="mt-2 space-y-2">
                      {(translatorNote?.action_items ?? []).length > 0 ? (translatorNote?.action_items ?? []).map((item) => (
                        <div key={item} className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-700">
                          {item}
                        </div>
                      )) : <span className="text-sm text-slate-500">No action items extracted.</span>}
                    </div>
                  </div>
                </CardContent>
              </Card>
            </section>
          ) : null}
        </>
      )}
    </main>
  );
}
