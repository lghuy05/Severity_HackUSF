"use client";

import { FormEvent, useEffect, useRef, useState } from "react";

import { AgentFlowPanel } from "@/components/AgentFlowPanel";
import { Chat } from "@/components/Chat";
import { EmergencyOverlay } from "@/components/EmergencyOverlay";
import { HospitalList } from "@/components/HospitalList";
import { InputBox } from "@/components/InputBox";
import { MapView } from "@/components/MapView";
import { VoiceButton } from "@/components/VoiceButton";
import { analyzeSymptoms } from "@/lib/api";
import type { AgentStep, AnalyzeResponse, ChatMessage } from "../../shared/types";

type AppState = "idle" | "processing" | "decision" | "results" | "emergency";

const INITIAL_STEPS: AgentStep[] = [
  { key: "voice", label: "Voice", status: "idle", detail: "Waiting for input" },
  { key: "language", label: "Language", status: "idle", detail: "Translation layer ready" },
  { key: "triage", label: "Triage", status: "idle", detail: "Clinical reasoning on standby" },
  { key: "navigation", label: "Navigation", status: "idle", detail: "Care search paused" },
  { key: "action", label: "Action", status: "idle", detail: "Next-step guidance pending" },
];

const DEMO_LOCATION = "San Francisco, CA";
const RESULTS_DELAY_MS = 1400;
const EMERGENCY_DELAY_MS = 1800;

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

function updateStep(
  steps: AgentStep[],
  key: string,
  status: AgentStep["status"],
  detail?: string,
): AgentStep[] {
  return steps.map((step) => (step.key === key ? { ...step, status, detail: detail ?? step.detail } : step));
}

function sleep(ms: number) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

export default function HomePage() {
  const [appState, setAppState] = useState<AppState>("idle");
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: "welcome",
      role: "assistant",
      content: "Describe what you feel. I’ll interpret it, assess urgency, and guide you to the right care path.",
    },
  ]);
  const [steps, setSteps] = useState<AgentStep[]>(INITIAL_STEPS);
  const [isListening, setIsListening] = useState(false);
  const [loading, setLoading] = useState(false);
  const [analysis, setAnalysis] = useState<AnalyzeResponse | null>(null);
  const recognitionRef = useRef<SpeechRecognition | null>(null);
  const flowTimeoutsRef = useRef<number[]>([]);

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
      setSteps((current) => updateStep(current, "voice", "done", "Voice converted to text"));
    };
    recognition.onend = () => setIsListening(false);
    recognitionRef.current = recognition;
  }, []);

  useEffect(() => {
    return () => {
      flowTimeoutsRef.current.forEach((timeout) => window.clearTimeout(timeout));
    };
  }, []);

  function scheduleTransition(nextState: AppState, delay: number) {
    const timeout = window.setTimeout(() => setAppState(nextState), delay);
    flowTimeoutsRef.current.push(timeout);
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!input.trim() || loading) {
      return;
    }

    flowTimeoutsRef.current.forEach((timeout) => window.clearTimeout(timeout));
    flowTimeoutsRef.current = [];

    const userInput = input.trim();
    const userMessage: ChatMessage = { id: crypto.randomUUID(), role: "user", content: userInput };

    setMessages((current) => [...current, userMessage]);
    setLoading(true);
    setAnalysis(null);
    setSteps(INITIAL_STEPS);
    setAppState("processing");
    setSteps((current) => updateStep(current, "voice", "running", "Listening..."));

    try {
      await sleep(350);
      setSteps((current) => updateStep(current, "voice", "done", "Listening complete"));
      setSteps((current) => updateStep(current, "language", "running", "Translating..."));

      await sleep(450);
      setSteps((current) => updateStep(current, "language", "done", "Meaning normalized"));
      setSteps((current) => updateStep(current, "triage", "running", "Analyzing symptoms..."));

      const result = await analyzeSymptoms({ text: userInput, location: DEMO_LOCATION });
      setAnalysis(result);

      await sleep(650);
      setSteps((current) => updateStep(current, "triage", "done", `Risk level: ${result.triage.risk_level}`));
      setSteps((current) => updateStep(current, "navigation", "running", "Finding care..."));

      await sleep(550);
      setSteps((current) => updateStep(current, "navigation", "done", `${result.navigation.hospitals.length} care options ready`));
      setSteps((current) => updateStep(current, "action", "running", "Preparing next step"));

      await sleep(500);
      setSteps((current) => updateStep(current, "action", "done", "Response ready"));
      setMessages((current) => [
        ...current,
        {
          id: crypto.randomUUID(),
          role: "assistant",
          content: `${result.triage.explanation} ${result.navigation.recommendation} ${result.provider_message}`,
        },
      ]);

      if (result.triage.risk_level === "high") {
        setAppState("emergency");
        scheduleTransition("results", EMERGENCY_DELAY_MS);
      } else {
        setAppState("decision");
        scheduleTransition("results", RESULTS_DELAY_MS);
      }

      setInput("");
    } catch (error) {
      void error;
      setMessages((current) => [
        ...current,
        {
          id: crypto.randomUUID(),
          role: "assistant",
          content: "The analysis request failed. Check that the FastAPI backend is running on port 8000.",
        },
      ]);
      setSteps(INITIAL_STEPS);
      setAppState("idle");
    } finally {
      setLoading(false);
    }
  }

  function handleVoiceToggle() {
    const recognition = recognitionRef.current;
    if (!recognition) {
      setInput("I feel chest pain and dizzy");
      setSteps((current) => updateStep(current, "voice", "done", "Voice mocked with fallback text"));
      return;
    }

    if (isListening) {
      recognition.stop();
      setIsListening(false);
      return;
    }

    setIsListening(true);
    setSteps((current) => updateStep(current, "voice", "running", "Listening"));
    recognition.start();
  }

  const showChat = appState !== "idle";
  const showDecision = Boolean(analysis) && (appState === "decision" || appState === "results" || appState === "emergency");
  const showResults = Boolean(analysis) && appState === "results";
  const riskTone =
    analysis?.triage.risk_level === "high"
      ? "border-rose-400/20 bg-rose-500/10 text-rose-300"
      : analysis?.triage.risk_level === "medium"
        ? "border-amber-400/20 bg-amber-500/10 text-amber-300"
        : "border-emerald-400/20 bg-emerald-500/10 text-emerald-300";

  return (
    <main className="relative min-h-screen overflow-hidden px-4 py-6 md:px-8 md:py-8">
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_20%_20%,rgba(59,130,246,0.08),transparent_20%),radial-gradient(circle_at_80%_10%,rgba(129,140,248,0.1),transparent_22%)]" />

      <AgentFlowPanel steps={steps} visible={appState !== "idle"} />
      <EmergencyOverlay
        instructions={analysis?.emergency.instructions ?? []}
        visible={appState === "emergency" || (appState === "results" && analysis?.triage.risk_level === "high")}
      />

      <div className="relative mx-auto flex min-h-[calc(100vh-3rem)] max-w-7xl items-center justify-center">
        <section className={["w-full transition-all duration-700", appState === "idle" ? "max-w-3xl" : "max-w-7xl"].join(" ")}>
          <div
            className={[
              "transition-all duration-700",
              appState === "idle" ? "flex min-h-[80vh] flex-col items-center justify-center text-center" : "space-y-6 pt-16",
            ].join(" ")}
          >
            <div className={appState === "idle" ? "max-w-2xl" : "max-w-3xl"}>
              <p className="text-[11px] font-semibold uppercase tracking-[0.34em] text-sky-200/70">Health Equity Bridge</p>
              <h1 className="mt-4 text-4xl font-semibold tracking-tight text-white md:text-6xl">
                From symptom uncertainty to a clear care decision.
              </h1>
              <p className="mt-4 text-base leading-7 text-slate-400 md:text-lg">
                A guided AI triage experience that listens, reasons, and reveals the right next action at the right moment.
              </p>
            </div>

            <div className={appState === "idle" ? "mt-10 w-full max-w-2xl" : "w-full"}>
              <InputBox value={input} disabled={loading} onChange={setInput} onSubmit={handleSubmit}>
                <VoiceButton isListening={isListening} onToggle={handleVoiceToggle} />
                <button
                  type="submit"
                  disabled={loading}
                  className="inline-flex h-14 items-center justify-center rounded-full bg-gradient-to-r from-sky-500 to-indigo-500 px-6 text-sm font-semibold text-white transition duration-300 hover:shadow-[0_0_30px_rgba(99,102,241,0.35)] disabled:cursor-not-allowed disabled:opacity-60"
                >
                  {loading ? "Analyzing..." : "Continue"}
                </button>
              </InputBox>

              {appState === "idle" ? (
                <p className="mt-4 text-sm text-slate-500">Try: “I feel chest pain and dizzy”</p>
              ) : null}
            </div>

            {showChat ? (
              <div className="w-full animate-fade-in space-y-6">
                <Chat messages={messages} isTyping={appState === "processing"} />

                {appState === "processing" ? (
                  <div className="rounded-[32px] border border-white/10 bg-white/5 p-5 text-left shadow-panel backdrop-blur-2xl">
                    <p className="text-[11px] font-semibold uppercase tracking-[0.3em] text-slate-500">Processing</p>
                    <div className="mt-4 grid gap-3 md:grid-cols-4">
                      {["Listening...", "Translating...", "Analyzing symptoms...", "Finding care..."].map((item, index) => (
                        <div
                          key={item}
                          className="animate-fade-in rounded-[22px] border border-white/8 bg-[#0E141C] p-4 text-sm text-slate-300"
                          style={{ animationDelay: `${index * 120}ms` }}
                        >
                          {item}
                        </div>
                      ))}
                    </div>
                  </div>
                ) : null}

                {showDecision ? (
                  <div className="animate-fade-in rounded-[32px] border border-white/10 bg-white/6 p-6 text-left shadow-panel backdrop-blur-2xl">
                    <p className="text-[11px] font-semibold uppercase tracking-[0.3em] text-slate-500">Decision</p>
                    <div className="mt-4 flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
                      <div className="max-w-3xl">
                        <h2 className="text-2xl font-semibold text-white">Here’s what the system sees right now.</h2>
                        <p className="mt-3 text-base leading-7 text-slate-300">{analysis?.triage.explanation}</p>
                        <p className="mt-3 text-sm leading-6 text-slate-400">{analysis?.navigation.recommendation}</p>
                      </div>
                      <div className={`rounded-full border px-4 py-2 text-sm font-semibold capitalize ${riskTone}`}>
                        {analysis?.triage.risk_level} risk
                      </div>
                    </div>
                  </div>
                ) : null}

                {showResults ? (
                  <div className="grid gap-6 xl:grid-cols-[1.05fr_0.95fr]">
                    <section className="space-y-6">
                      <div className="rounded-[32px] border border-white/10 bg-white/6 p-6 shadow-panel backdrop-blur-2xl">
                        <p className="text-[11px] font-semibold uppercase tracking-[0.3em] text-slate-500">Explanation</p>
                        <div className="mt-4 space-y-4">
                          <div className="rounded-[24px] border border-white/8 bg-[#0E141C] p-4">
                            <p className="text-sm font-medium text-slate-400">Detected language</p>
                            <p className="mt-1 text-lg font-semibold text-white">{analysis?.language_output.detected_language}</p>
                          </div>
                          <div className="rounded-[24px] border border-white/8 bg-[#0E141C] p-4">
                            <p className="text-sm font-medium text-slate-400">AI summary</p>
                            <p className="mt-2 text-sm leading-6 text-slate-200">{analysis?.provider_message}</p>
                          </div>
                        </div>
                      </div>
                    </section>

                    <section className="space-y-4 animate-slide-in-right">
                      <div className="rounded-[32px] border border-white/10 bg-white/6 p-5 shadow-panel backdrop-blur-2xl">
                        <div className="flex items-center justify-between">
                          <div>
                            <p className="text-[11px] font-semibold uppercase tracking-[0.3em] text-slate-500">Nearby care</p>
                            <h2 className="mt-1 text-xl font-semibold text-white">Hospital map</h2>
                          </div>
                          <span className="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs text-slate-300">
                            {DEMO_LOCATION}
                          </span>
                        </div>

                        <div className="mt-4 animate-fade-in">
                          <MapView location={DEMO_LOCATION} />
                        </div>
                      </div>

                      <HospitalList hospitals={analysis?.navigation.hospitals ?? []} />
                    </section>
                  </div>
                ) : null}
              </div>
            ) : null}
          </div>
        </section>
      </div>
    </main>
  );
}
