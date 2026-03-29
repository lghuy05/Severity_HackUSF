"use client";

import type { AnalyzeResponse, AssistantTurnPayload, ChatMessage, ChatSessionState, QuickAction, UserProfile } from "@shared/types";

const CHAT_STATE_KEY = "heb.chat.state";
const PROFILE_KEY = "heb.user.profile";

export type PersistedChatState = {
  messages: ChatMessage[];
  session: ChatSessionState | null;
  suggestedActions: QuickAction[];
  uiBlocks: string[];
  analysis: AnalyzeResponse | null;
  assistantTurn: AssistantTurnPayload | null;
  activePanel: "care" | "cost" | null;
};

export const DEFAULT_PROFILE: UserProfile = {
  language: "en",
  location: "",
  age: null,
  gender: null,
};

export function saveChatState(state: PersistedChatState) {
  if (typeof window === "undefined") return;
  window.sessionStorage.setItem(CHAT_STATE_KEY, JSON.stringify(state));
}

export function loadChatState(): PersistedChatState | null {
  if (typeof window === "undefined") return null;
  const raw = window.sessionStorage.getItem(CHAT_STATE_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as PersistedChatState;
  } catch {
    return null;
  }
}

export function saveUserProfile(profile: UserProfile) {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(PROFILE_KEY, JSON.stringify(profile));
}

export function loadUserProfile(): UserProfile {
  if (typeof window === "undefined") return DEFAULT_PROFILE;
  const raw = window.localStorage.getItem(PROFILE_KEY);
  if (!raw) return DEFAULT_PROFILE;
  try {
    return { ...DEFAULT_PROFILE, ...(JSON.parse(raw) as UserProfile) };
  } catch {
    return DEFAULT_PROFILE;
  }
}
