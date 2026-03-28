"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { ArrowRight, ShieldAlert, Sparkles } from "lucide-react";

import { AgentFlow } from "@/components/AgentFlow";
import { ChatView } from "@/components/ChatView";
import { CostPanel } from "@/components/CostPanel";
import { EmergencyOverlay } from "@/components/EmergencyOverlay";
import { InputBar } from "@/components/InputBar";
import { MapPanel } from "@/components/MapPanel";
import { ProfilePanel } from "@/components/ProfilePanel";
import { StepTransition } from "@/components/StepTransition";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { analyzeSymptoms } from "@/lib/api";
import type { AnalyzeResponse, ChatMessage } from "@shared/types";

type AppState = "idle" | "processing" | "diagnosis" | "navigation" | "cost" | "contact" | "emergency";

const PROCESSING_STEPS = [
  { step: "voice", label: "Understanding symptoms..." },
  { step: "language", label: "Translating..." },
  { step: "triage", label: "Analyzing risk..." },
] as const;

const SAMPLE_PROMPT = "I feel chest pain and dizzy";
const DEFAULT_LOCATION = "San Francisco, CA";

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
    start(): void;
    stop(): void;
  }

  interface SpeechRecognitionEvent {
    results: ArrayLike<ArrayLike<{ transcript: string }>>;
  }
}

function wait(ms: number) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function buildDiagnosisMessages(result: AnalyzeResponse): ChatMessage[] {
  return [
    {
      id: "assistant-diagnosis",
      role: "assistant",
      content: `I simplified your symptoms as: "${result.language_output.simplified_text}".`,
    },
    {
      id: "assistant-triage",
      role: "assistant",
      content: `${result.triage.explanation} ${result.navigation.recommendation}`,
    },
    {
      id: "assistant-provider",
      role: "assistant",
      content: result.provider_message,
    },
  ];
}

export default function Page() {
  const [appState, setAppState] = useState<AppState>("idle");
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [activeFlowStep, setActiveFlowStep] = useState<string>("voice");
  const [processingLabel, setProcessingLabel] = useState<string>(PROCESSING_STEPS[0].label);
  const [isListening, setIsListening] = useState(false);
  const [isTyping, setIsTyping] = useState(false);
  const [analysis, setAnalysis] = useState<AnalyzeResponse | null>(null);
  const [profileSent, setProfileSent] = useState(false);
  const [showEmergencyOverlay, setShowEmergencyOverlay] = useState(false);
  const recognitionRef = useRef<SpeechRecognition | null>(null);

  useEffect(() => {
    const Recognition = window.SpeechRecognition ?? window.webkitSpeechRecognition;
    if (!Recognition) {
      return;
    }

    const recognition = new Recognition();
    recognition.lang = "en-US";
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.onresult = (event) => {
      const transcript = event.results[0]?.[0]?.transcript ?? "";
      setInput(transcript);
      setIsListening(false);
    };
    recognition.onend = () => setIsListening(false);
    recognitionRef.current = recognition;
  }, []);

  const hospitals = analysis?.navigation.hospitals ?? [];
  const riskLevel = analysis?.triage.risk_level;
  const heroTitle = useMemo(
    () => ["A calmer path", "from symptoms", "to care."],
    [],
  );

  async function startFlow(prompt?: string) {
    const nextInput = (prompt ?? input).trim();
    if (!nextInput) {
      return;
    }

    const userMessage: ChatMessage = {
      id: crypto.randomUUID(),
      role: "user",
      content: nextInput,
    };

    setInput("");
    setAnalysis(null);
    setProfileSent(false);
    setShowEmergencyOverlay(false);
    setMessages([userMessage]);
    setAppState("processing");
    setIsTyping(true);
    setActiveFlowStep("voice");
    setProcessingLabel(PROCESSING_STEPS[0].label);

    try {
      for (const item of PROCESSING_STEPS) {
        setActiveFlowStep(item.step);
        setProcessingLabel(item.label);
        await wait(700);
      }

      const result = await analyzeSymptoms({ text: nextInput, location: DEFAULT_LOCATION });
      setAnalysis(result);
      setMessages((current) => [...current, ...buildDiagnosisMessages(result)]);
      setIsTyping(false);

      if (result.emergency_flag || result.triage.risk_level === "high") {
        setActiveFlowStep("action");
        setAppState("emergency");
        return;
      }

      setAppState("diagnosis");
      setActiveFlowStep("triage");
      await wait(1100);
      setAppState("navigation");
      setActiveFlowStep("navigation");
      await wait(1100);
      setAppState("cost");
      await wait(1100);
      setAppState("contact");
      setActiveFlowStep("action");
    } catch {
      setIsTyping(false);
      setAppState("diagnosis");
      setAnalysis(null);
      setMessages((current) => [
        ...current,
        {
          id: crypto.randomUUID(),
          role: "assistant",
          content: "I couldn’t reach `/api/analyze` right now. The frontend flow is ready, but the backend needs to be connected.",
        },
      ]);
    }
  }

  function handleVoiceToggle() {
    const recognition = recognitionRef.current;
    if (!recognition) {
      setInput(SAMPLE_PROMPT);
      return;
    }

    if (isListening) {
      recognition.stop();
      setIsListening(false);
      return;
    }

    recognition.start();
    setIsListening(true);
  }

  return (
    <main className="relative min-h-screen overflow-hidden bg-[#0b0f14] text-white">
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_top,rgba(56,189,248,0.18),transparent_28%),radial-gradient(circle_at_85%_16%,rgba(129,140,248,0.16),transparent_24%),linear-gradient(180deg,#0b0f14_0%,#0d1320_48%,#0b0f14_100%)]" />
      <div className="absolute inset-0 bg-[linear-gradient(rgba(255,255,255,0.02)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.02)_1px,transparent_1px)] bg-[size:120px_120px] opacity-[0.18]" />

      <AgentFlow activeStep={activeFlowStep} visible={appState !== "idle"} />
      <EmergencyOverlay
        open={showEmergencyOverlay}
        instructions={analysis?.emergency.instructions ?? ["Call 911 immediately.", "Do not drive yourself.", "Stay with someone if possible."]}
        onClose={() => setShowEmergencyOverlay(false)}
      />

      <div className="relative z-10 mx-auto flex min-h-screen w-full max-w-7xl flex-col px-4 pb-8 pt-8 sm:px-6 lg:px-8">
        {appState === "idle" ? (
          <section className="flex flex-1 flex-col items-center justify-center text-center">
            <Badge className="mb-6">AI healthcare navigator</Badge>
            <div className="max-w-4xl">
              <h1 className="text-balance text-5xl font-semibold tracking-[-0.05em] text-white sm:text-6xl lg:text-7xl">
                {heroTitle[0]} <span className="bg-gradient-to-r from-sky-200 via-white to-violet-200 bg-clip-text text-transparent">{heroTitle[1]}</span>{" "}
                {heroTitle[2]}
              </h1>
              <p className="mx-auto mt-6 max-w-2xl text-base leading-8 text-slate-300 sm:text-lg">
                Describe symptoms once. The system simplifies, translates, diagnoses urgency, finds care, compares cost,
                and prepares a hospital handoff without dumping every panel on screen at once.
              </p>
            </div>

            <div className="mt-10 w-full max-w-4xl">
              <InputBar
                value={input}
                onChange={setInput}
                onSubmit={() => void startFlow()}
                onVoiceToggle={handleVoiceToggle}
                isListening={isListening}
                compact={false}
              />
            </div>

            <div className="mt-5 flex flex-wrap items-center justify-center gap-3 text-sm text-slate-400">
              <button
                type="button"
                onClick={() => {
                  setInput(SAMPLE_PROMPT);
                  void startFlow(SAMPLE_PROMPT);
                }}
                className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/[0.06] px-4 py-2 transition hover:bg-white/10"
              >
                Try sample flow
                <ArrowRight className="h-4 w-4" />
              </button>
              <span className="inline-flex items-center gap-2">
                <Sparkles className="h-4 w-4 text-sky-300" />
                Voice, translation, triage, routing, cost, contact
              </span>
            </div>
          </section>
        ) : (
          <section className="grid flex-1 gap-6 pt-20 lg:grid-cols-[minmax(0,1.08fr)_minmax(360px,0.92fr)]">
            <div className="flex min-h-0 flex-col gap-5">
              <div className="rounded-[30px] border border-white/10 bg-white/[0.045] p-4 shadow-[0_24px_80px_rgba(4,9,22,0.35)] backdrop-blur-2xl">
                {appState === "processing" ? (
                  <div className="flex items-center justify-between gap-4 rounded-[24px] bg-[#0f1726]/84 px-5 py-5">
                    <div>
                      <p className="text-xs uppercase tracking-[0.24em] text-slate-500">Agent status</p>
                      <p className="mt-2 text-lg font-medium text-white">{processingLabel}</p>
                    </div>
                    <div className="flex items-center gap-2 rounded-full border border-emerald-400/[0.18] bg-emerald-500/[0.10] px-4 py-2 text-sm text-emerald-200">
                      <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
                      Processing
                    </div>
                  </div>
                ) : null}

                <ChatView
                  messages={messages}
                  isTyping={isTyping}
                  riskLevel={riskLevel}
                  title={appState === "processing" ? "Analyzing your request" : "Guided care conversation"}
                />
              </div>

              <div className="sticky bottom-0">
                <InputBar
                  value={input}
                  onChange={setInput}
                  onSubmit={() => void startFlow()}
                  onVoiceToggle={handleVoiceToggle}
                  isListening={isListening}
                  isBusy={appState === "processing"}
                  compact
                />
              </div>
            </div>

            <div className="space-y-5">
              <StepTransition show={appState === "navigation" || appState === "cost" || appState === "contact" || appState === "emergency"}>
                <MapPanel hospitals={hospitals.length ? hospitals : [{ name: "Closest hospital", address: "San Francisco General Hospital, San Francisco, CA", lat: 37.7557, lng: -122.4044, phone: "(415) 206-8000" }]} />
              </StepTransition>

              <StepTransition show={appState === "cost" || appState === "contact"}>
                <CostPanel hospitals={hospitals.length ? hospitals : [{ name: "Closest hospital", address: "San Francisco General Hospital, San Francisco, CA", lat: 37.7557, lng: -122.4044, phone: "(415) 206-8000" }]} riskLevel={riskLevel} />
              </StepTransition>

              <StepTransition show={appState === "contact"}>
                <ProfilePanel onSend={() => setProfileSent(true)} sent={profileSent} />
              </StepTransition>

              {appState === "emergency" ? (
                <div className="animate-fade-in rounded-[28px] border border-rose-400/[0.20] bg-rose-500/[0.10] p-5 text-sm text-rose-100">
                  <div className="mb-2 flex items-center gap-2 font-medium">
                    <ShieldAlert className="h-4 w-4" />
                    Emergency mode
                  </div>
                  <p className="leading-7">
                    This case is flagged as urgent. The experience stays in place, and emergency guidance is available
                    without forcing a modal open.
                  </p>
                  <div className="mt-4 flex flex-col gap-3 sm:flex-row">
                    <Button asChild variant="emergency" className="gap-2">
                      <a href="tel:911">Call 911</a>
                    </Button>
                    <Button variant="secondary" onClick={() => setShowEmergencyOverlay(true)}>
                      View emergency instructions
                    </Button>
                  </div>
                </div>
              ) : null}
            </div>
          </section>
        )}
      </div>
    </main>
  );
}
