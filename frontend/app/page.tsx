"use client";

import Link from "next/link";
import { useEffect, useMemo, useRef, useState } from "react";
import { Globe2, Mic, ShieldAlert } from "lucide-react";

import { ChatView } from "@/components/ChatView";
import { ConversationCareOptions } from "@/components/ConversationCareOptions";
import { EmergencyOverlay } from "@/components/EmergencyOverlay";
import { InputBar } from "@/components/InputBar";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { streamChatTurn } from "@/lib/api";
import { getUiCopy, speechLocaleFor, type UiLanguage } from "@/lib/i18n";
import { saveLatestAnalysis, saveLatestContext } from "@/lib/latest-analysis";
import { DEFAULT_PROFILE, loadChatState, loadUserProfile, saveChatState, saveUserProfile } from "@/lib/session-store";
import type { AnalyzeResponse, AssistantTurnPayload, ChatIntent, ChatMessage, ChatSessionState, UserProfile } from "@shared/types";

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

function sessionToAnalysis(session: ChatSessionState, agentFlow: AnalyzeResponse["agent_flow"], trace: AnalyzeResponse["trace"]): AnalyzeResponse {
  const structuredSymptom = session.state.symptom ?? session.normalized_text ?? session.raw_text ?? "";
  const structuredRisk = (session.state.risk as "low" | "medium" | "high" | null) ?? session.risk_level ?? "low";
  return {
    request_id: session.request_id ?? crypto.randomUUID(),
    language_output: {
      detected_language: session.detected_language ?? "en",
      simplified_text: structuredSymptom,
      translated_text: structuredSymptom,
    },
    triage: {
      risk_level: structuredRisk,
      explanation: session.risk_reason ?? "",
    },
    navigation: {
      origin: session.location,
      recommendation: structuredRisk === "high" ? "Head to the nearest emergency department now." : "Here are nearby care options based on your location.",
      hospitals: session.hospitals,
    },
    summary: {
      patient_input: session.raw_text ?? "",
      location: session.location,
      detected_language: session.detected_language ?? "en",
      normalized_text: structuredSymptom,
      risk_level: structuredRisk,
      triage_explanation: session.risk_reason ?? "",
      recommended_sites: session.hospitals.map((hospital) => hospital.name),
      emergency_flag: session.emergency_flag,
      emergency_instructions: session.emergency_instructions,
    },
    provider_message: session.provider_summary ?? "",
    emergency_flag: session.emergency_flag,
    emergency: {
      emergency_flag: session.emergency_flag,
      instructions: session.emergency_instructions,
    },
    cost_options: session.cost_options,
    agent_flow: agentFlow,
    trace,
  };
}

export default function Page() {
  const [input, setInput] = useState("");
  const [language, setLanguage] = useState<UiLanguage>("en");
  const [profile, setProfile] = useState<UserProfile>(DEFAULT_PROFILE);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [session, setSession] = useState<ChatSessionState | null>(null);
  const [assistantTurn, setAssistantTurn] = useState<AssistantTurnPayload | null>(null);
  const [analysis, setAnalysis] = useState<AnalyzeResponse | null>(null);
  const [isListening, setIsListening] = useState(false);
  const [voiceAvailable, setVoiceAvailable] = useState(false);
  const [isTyping, setIsTyping] = useState(false);
  const [showEmergencyOverlay, setShowEmergencyOverlay] = useState(false);
  const recognitionRef = useRef<SpeechRecognition | null>(null);

  const copy = useMemo(() => getUiCopy(language), [language]);
  const showCarePanel = Boolean(analysis && assistantTurn?.ui_blocks.includes("care_options"));

  function handleLanguageChange(nextLanguage: UiLanguage) {
    setLanguage(nextLanguage);
    setProfile((current) => {
      const nextProfile = { ...current, language: nextLanguage };
      saveUserProfile(nextProfile);
      return nextProfile;
    });
  }

  useEffect(() => {
    const savedProfile = loadUserProfile();
    setProfile(savedProfile);
    if (savedProfile.language) {
      setLanguage(savedProfile.language as UiLanguage);
    }

    const savedChat = loadChatState();
    if (savedChat) {
      setMessages(savedChat.messages);
      setSession(savedChat.session);
      setAssistantTurn(savedChat.assistantTurn ?? null);
      setAnalysis(savedChat.analysis);
    }
  }, []);

  useEffect(() => {
    const Recognition = window.SpeechRecognition ?? window.webkitSpeechRecognition;
    if (!Recognition) {
      setVoiceAvailable(false);
      return;
    }

    const recognition = new Recognition();
    recognition.lang = speechLocaleFor(language);
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.onresult = (event) => {
      const transcript = event.results[0]?.[0]?.transcript ?? "";
      setInput(transcript);
      setIsListening(false);
    };
    recognition.onend = () => setIsListening(false);
    recognitionRef.current = recognition;
    setVoiceAvailable(true);

    return () => {
      recognition.stop();
    };
  }, [language]);

  async function runIntent(intent: ChatIntent, prompt?: string) {
    const nextLocation = (profile.location || "").trim();
    const nextMessage = (prompt ?? input).trim();

    if (!nextLocation) {
      return;
    }
    if (intent === "symptoms" && !nextMessage) {
      return;
    }

    if (intent === "symptoms") {
      setMessages((current) =>
        current.length === 0
          ? [{ id: crypto.randomUUID(), role: "user", content: nextMessage }]
          : [...current, { id: crypto.randomUUID(), role: "user", content: nextMessage }],
      );
      saveLatestContext({ text: nextMessage, location: nextLocation });
    } else {
      const action = assistantTurn?.actions.find((item) => item.intent === intent);
      const userText = prompt ?? action?.label ?? intent;
      setMessages((current) => [...current, { id: crypto.randomUUID(), role: "user", content: userText }]);
    }

    setIsTyping(true);
    const pendingAssistantId = crypto.randomUUID();
    setMessages((current) => [...current, { id: pendingAssistantId, role: "assistant", content: "" }]);

    try {
      const final = await streamChatTurn(
        {
          intent,
          message: intent === "symptoms" ? nextMessage : prompt,
          location: nextLocation,
          preferred_language: language,
          profile: {
            ...profile,
            language,
            location: nextLocation,
          },
        },
        (chunk) => {
          if (chunk.type === "message" && chunk.message) {
            setMessages((current) =>
              current.map((message) =>
                message.id === pendingAssistantId
                  ? { ...message, content: `${message.content}${message.content ? "\n\n" : ""}${chunk.message}` }
                  : message,
              ),
            );
          }

          if (chunk.type === "done" && chunk.session) {
            setSession(chunk.session);
            setAssistantTurn(chunk.response);
            const snapshot = sessionToAnalysis(chunk.session, chunk.agent_flow, chunk.trace);
            setAnalysis(snapshot);
            saveLatestAnalysis(snapshot);
          }
        },
      );

      setSession(final.session);
      setAssistantTurn(final.response);
      const snapshot = sessionToAnalysis(final.session, final.agent_flow, final.trace);
      setAnalysis(snapshot);
      saveLatestAnalysis(snapshot);
    } catch {
      setMessages((current) =>
        current.map((message) =>
          message.id === pendingAssistantId ? { ...message, content: copy.errorMessage } : message,
        ),
      );
    } finally {
      setIsTyping(false);
      if (intent === "symptoms") {
        setInput("");
      }
    }
  }

  useEffect(() => {
    saveChatState({
      messages,
      session,
      suggestedActions: assistantTurn?.actions ?? [],
      uiBlocks: assistantTurn?.ui_blocks ?? [],
      analysis,
      assistantTurn,
      activePanel: null,
    });
  }, [messages, session, assistantTurn, analysis]);

  function handleVoiceToggle() {
    const recognition = recognitionRef.current;
    if (!recognition || !voiceAvailable) {
      return;
    }

    if (isListening) {
      recognition.stop();
      setIsListening(false);
      return;
    }

    recognition.lang = speechLocaleFor(language);
    recognition.start();
    setIsListening(true);
  }

  const embeddedMessages = analysis
    ? [
        assistantTurn?.follow_up ? (
          <div key="follow-up" className="space-y-3 rounded-[28px] border border-slate-200 bg-white p-5 shadow-[0_12px_30px_rgba(148,163,184,0.10)]">
            <p className="text-sm font-medium text-slate-950">{assistantTurn.follow_up.text}</p>
            <div className="flex flex-wrap gap-3">
              {assistantTurn.follow_up.options.map((option) => (
                <Button key={option} variant="secondary" onClick={() => void runIntent("symptoms", option)}>
                  {option}
                </Button>
              ))}
            </div>
          </div>
        ) : null,
        assistantTurn?.ui_blocks.includes("emergency") ? (
          <div key="emergency" className="rounded-[32px] border border-rose-200 bg-rose-50/90 p-6 text-rose-800 shadow-[0_22px_60px_rgba(244,63,94,0.08)]">
            <div className="mb-2 flex items-center gap-2 text-sm font-semibold uppercase tracking-[0.18em] text-rose-600">
              <ShieldAlert className="h-4 w-4" />
              {copy.urgentGuidance}
            </div>
            <p className="text-sm leading-7">{copy.urgentBody}</p>
            <div className="mt-5 flex flex-col gap-3 sm:flex-row">
              <Button asChild variant="emergency">
                <a href="tel:911">{copy.callEmergency}</a>
              </Button>
              <Button variant="secondary" onClick={() => setShowEmergencyOverlay(true)}>
                {copy.viewEmergencyInstructions}
              </Button>
            </div>
          </div>
        ) : null,
        assistantTurn?.actions.length ? (
          <div key="actions" className="flex flex-wrap gap-3">
            {assistantTurn.actions.map((action) => (
              <Button
                key={action.intent}
                variant="secondary"
                onClick={() => void runIntent(action.intent, action.prompt ?? undefined)}
              >
                {action.label}
              </Button>
            ))}
          </div>
        ) : null,
      ].filter(Boolean)
    : [];

  return (
    <main className="app-shell-gradient min-h-screen">
      <EmergencyOverlay
        open={showEmergencyOverlay}
        instructions={copy.emergencyInstructions}
        onClose={() => setShowEmergencyOverlay(false)}
      />

      <div className="mx-auto flex min-h-[calc(100vh-81px)] w-full max-w-6xl flex-col px-4 pb-16 pt-10 sm:px-6 lg:px-8">
        <section className="flex flex-col items-center gap-8 pt-10 text-center sm:pt-16">
          <Badge className="border-sky-200 bg-sky-50 text-sky-700">{copy.appBadge}</Badge>
          <div className="max-w-4xl">
            <h1 className="text-balance text-5xl font-semibold tracking-[-0.05em] text-slate-950 sm:text-6xl lg:text-7xl">
              {copy.headline}
            </h1>
            <p className="mx-auto mt-6 max-w-2xl text-lg leading-8 text-slate-600">{copy.subtext}</p>
          </div>
        </section>

        <section className={`mx-auto mt-16 w-full ${showCarePanel ? "max-w-7xl" : "max-w-3xl"}`}>
          <div className={`grid gap-8 ${showCarePanel ? "lg:grid-cols-[minmax(0,1.05fr)_420px]" : "grid-cols-1"}`}>
            <div className="flex min-w-0 flex-col gap-6">
              <ChatView
                messages={messages}
                isTyping={isTyping}
                riskLevel={(session?.state.risk as "low" | "medium" | "high" | undefined) ?? analysis?.triage.risk_level}
                title={isTyping ? copy.reviewingTitle : copy.conversationTitle}
                assistantLabel={copy.careAssistant}
                reviewingLabel={copy.reviewing}
                embeddedMessages={embeddedMessages}
              />

              <div className="space-y-4">
                <InputBar
                  value={input}
                  onChange={setInput}
                  language={language}
                  onLanguageChange={(value) => handleLanguageChange(value as UiLanguage)}
                  onSubmit={() => void runIntent("symptoms")}
                  onVoiceToggle={handleVoiceToggle}
                  isListening={isListening}
                  voiceAvailable={voiceAvailable}
                  isBusy={isTyping}
                  promptPlaceholder={copy.promptPlaceholder}
                  continueLabel={copy.continue}
                  voiceUnavailableTitle={copy.voiceUnavailable}
                  canSubmit={Boolean(profile.location?.trim())}
                />

                <div className="flex flex-wrap items-center justify-center gap-4 text-sm text-slate-500">
                  {profile.location ? <span>{copy.locationUsing(profile.location)}</span> : null}
                  <span className="inline-flex items-center gap-2">
                    <Mic className="h-4 w-4 text-slate-400" />
                    {voiceAvailable ? copy.voiceReady : copy.voiceUnavailable}
                  </span>
                  <span className="inline-flex items-center gap-2">
                    <Globe2 className="h-4 w-4 text-slate-400" />
                    {language.toUpperCase()}
                  </span>
                  {profile.age ? <span>Age {profile.age}</span> : null}
                  {profile.gender ? <span>{profile.gender}</span> : null}
                  {!profile.location ? (
                    <Button asChild variant="ghost" className="h-auto px-0 text-sm text-sky-700 hover:text-sky-800">
                      <Link href="/profile">Add your location in profile</Link>
                    </Button>
                  ) : null}
                </div>
              </div>
            </div>

            {showCarePanel && analysis ? (
              <aside className="min-w-0">
                <div className="sticky top-24 rounded-[32px] border border-slate-200/80 bg-white/92 p-5 shadow-[0_28px_80px_rgba(148,163,184,0.14)] backdrop-blur-xl">
                  <ConversationCareOptions
                    analysis={analysis}
                    copy={copy}
                    defaultShowCosts={Boolean(assistantTurn?.ui_blocks.includes("costs"))}
                  />
                </div>
              </aside>
            ) : null}
          </div>
        </section>

        <div className="mt-10 flex justify-center">
          <Button asChild variant="ghost" className="text-slate-500">
            <Link href="/debug">{copy.systemView}</Link>
          </Button>
        </div>
      </div>
    </main>
  );
}
