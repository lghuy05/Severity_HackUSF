"use client";

import { FormEvent, useEffect, useRef, useState } from "react";

import { AgentFlowPanel } from "@/components/AgentFlowPanel";
import { ChatPanel } from "@/components/ChatPanel";
import { EmergencyBanner } from "@/components/EmergencyBanner";
import { MapPanel } from "@/components/MapPanel";
import { VoiceInputButton } from "@/components/VoiceInputButton";
import { analyzeSymptoms, communicateSummary } from "@/lib/api";
import type { AgentStep, AnalyzeResponse, ChatMessage } from "../../shared/types";

const INITIAL_STEPS: AgentStep[] = [
  { key: "voice", label: "Voice Agent", status: "idle", detail: "Listening for voice or text input" },
  { key: "language", label: "Language Agent", status: "idle" },
  { key: "triage", label: "Triage Agent", status: "idle" },
  { key: "navigation", label: "Navigation Agent", status: "idle" },
  { key: "summary", label: "Summary Agent", status: "idle" },
  { key: "communication", label: "Communication Agent", status: "idle" },
];

const DEMO_LOCATION = "San Francisco, CA";

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

export default function HomePage() {
  const [input, setInput] = useState("");
  const [location, setLocation] = useState(DEMO_LOCATION);
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: "welcome",
      role: "assistant",
      content: "Describe symptoms by voice or chat. I will triage the concern, surface nearby hospitals, and prepare a provider-ready summary.",
    },
  ]);
  const [steps, setSteps] = useState<AgentStep[]>(INITIAL_STEPS);
  const [isListening, setIsListening] = useState(false);
  const [loading, setLoading] = useState(false);
  const [analysis, setAnalysis] = useState<AnalyzeResponse | null>(null);
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
      setSteps((current) => updateStep(current, "voice", "done", "Voice converted to text"));
    };
    recognition.onend = () => setIsListening(false);
    recognitionRef.current = recognition;
  }, []);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!input.trim() || loading) {
      return;
    }

    const userMessage: ChatMessage = { id: crypto.randomUUID(), role: "user", content: input };
    setMessages((current) => [...current, userMessage]);
    setLoading(true);
    setAnalysis(null);
    setSteps((current) => updateStep(current, "voice", "done", "Input captured"));
    setSteps((current) => updateStep(current, "language", "running", "Normalizing language"));

    try {
      await new Promise((resolve) => setTimeout(resolve, 250));
      setSteps((current) => updateStep(current, "language", "done", "Language simplified"));
      setSteps((current) => updateStep(current, "triage", "running", "Assessing risk"));

      await new Promise((resolve) => setTimeout(resolve, 250));
      const result = await analyzeSymptoms({ text: input, location });
      setAnalysis(result);

      setSteps((current) => updateStep(current, "triage", "done", `Risk: ${result.triage.risk_level}`));
      setSteps((current) => updateStep(current, "navigation", "running", "Finding nearby hospitals"));

      await new Promise((resolve) => setTimeout(resolve, 250));
      setSteps((current) => updateStep(current, "navigation", "done", `${result.navigation.hospitals.length} hospitals ready`));
      setSteps((current) => updateStep(current, "summary", "running", "Building structured summary"));

      await new Promise((resolve) => setTimeout(resolve, 250));
      setSteps((current) => updateStep(current, "summary", "done", "Summary JSON prepared"));
      setSteps((current) => updateStep(current, "communication", "running", "Formatting provider handoff"));

      const provider = await communicateSummary(result.summary);
      setSteps((current) => updateStep(current, "communication", "done", "Provider message ready"));
      setMessages((current) => [
        ...current,
        {
          id: crypto.randomUUID(),
          role: "assistant",
          content: `${result.triage.explanation} ${result.navigation.recommendation} Provider handoff: ${provider.message}`,
        },
      ]);
      setInput("");
    } catch (error) {
      setMessages((current) => [
        ...current,
        {
          id: crypto.randomUUID(),
          role: "assistant",
          content: "The analysis request failed. Check that the FastAPI backend is running on port 8000.",
        },
      ]);
      setSteps(INITIAL_STEPS);
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

  return (
    <main className="min-h-screen px-4 py-6 md:px-8">
      <div className="mx-auto max-w-7xl">
        <section className="rounded-[36px] border border-white/60 bg-white/50 p-6 shadow-panel backdrop-blur md:p-8">
          <div className="flex flex-col gap-8 lg:flex-row lg:items-end lg:justify-between">
            <div className="max-w-3xl">
              <p className="text-xs font-semibold uppercase tracking-[0.3em] text-slate-500">Health Equity Bridge</p>
              <h1 className="mt-3 text-4xl font-semibold tracking-tight text-ink md:text-5xl">
                AI multi-agent healthcare navigation for voice, chat, triage, and urgent action.
              </h1>
              <p className="mt-4 max-w-2xl text-base leading-7 text-slate-600">
                Demo-ready orchestration inspired by Google ADK + A2A concepts: perception, reasoning, and action in one clean operator view.
              </p>
            </div>

            <div className="rounded-[28px] bg-ink p-5 text-white">
              <p className="text-sm text-slate-200">Demo input</p>
              <p className="mt-2 text-lg font-semibold">“I feel chest pain and dizzy”</p>
            </div>
          </div>
        </section>

        <section className="mt-6 grid gap-6 xl:grid-cols-[1.15fr_0.85fr]">
          <div className="space-y-6">
            {analysis?.emergency_flag ? <EmergencyBanner instructions={analysis.emergency.instructions} /> : null}

            <form onSubmit={handleSubmit} className="rounded-[28px] bg-white/90 p-5 shadow-panel backdrop-blur">
              <div className="grid gap-4 md:grid-cols-[1fr_auto]">
                <div className="space-y-4">
                  <div>
                    <label className="mb-2 block text-sm font-medium text-slate-600">Symptoms</label>
                    <textarea
                      value={input}
                      onChange={(event) => setInput(event.target.value)}
                      placeholder="Describe symptoms or use voice input"
                      className="min-h-28 w-full rounded-3xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-ink outline-none transition focus:border-aqua"
                    />
                  </div>
                  <div>
                    <label className="mb-2 block text-sm font-medium text-slate-600">Location</label>
                    <input
                      value={location}
                      onChange={(event) => setLocation(event.target.value)}
                      className="w-full rounded-full border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-ink outline-none transition focus:border-aqua"
                    />
                  </div>
                </div>

                <div className="flex flex-col justify-between gap-3">
                  <VoiceInputButton isListening={isListening} onToggle={handleVoiceToggle} />
                  <button
                    type="submit"
                    disabled={loading}
                    className="rounded-full bg-ink px-5 py-3 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:opacity-60"
                  >
                    {loading ? "Analyzing..." : "Analyze"}
                  </button>
                </div>
              </div>
            </form>

            <div className="grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">
              <ChatPanel messages={messages} />
              <AgentFlowPanel steps={steps} />
            </div>

            {analysis ? (
              <div className="rounded-[28px] bg-white/90 p-5 shadow-panel backdrop-blur">
                <p className="text-xs font-semibold uppercase tracking-[0.24em] text-slate-500">System Summary</p>
                <div className="mt-4 grid gap-4 md:grid-cols-2">
                  <div className="rounded-2xl bg-mist p-4">
                    <p className="text-sm font-medium text-slate-500">Detected language</p>
                    <p className="mt-1 text-lg font-semibold text-ink">{analysis.language_output.detected_language}</p>
                  </div>
                  <div className="rounded-2xl bg-mist p-4">
                    <p className="text-sm font-medium text-slate-500">Risk level</p>
                    <p className="mt-1 text-lg font-semibold capitalize text-ink">{analysis.triage.risk_level}</p>
                  </div>
                </div>
                <p className="mt-4 text-sm leading-7 text-slate-600">{analysis.triage.explanation}</p>
              </div>
            ) : null}
          </div>

          <div className="space-y-6">
            <MapPanel hospitals={analysis?.navigation.hospitals ?? []} location={location} />
          </div>
        </section>
      </div>
    </main>
  );
}
