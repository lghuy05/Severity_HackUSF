"use client";

import type { AnalyzeResponse, AssistantTurnPayload, ChatMessage, ChatSessionState, QuickAction, UserProfile } from "@shared/types";

const CHAT_STATE_KEY = "heb.chat.state";
const PROFILE_KEY = "heb.user.profile";
const USER_ID_KEY = "heb.user.id";

function readStorage(key: string) {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(key) ?? window.sessionStorage.getItem(key);
}

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
  name: "User",
  language: "en",
  location: "",
  age: null,
  gender: null,
};

export function saveChatState(state: PersistedChatState) {
  if (typeof window === "undefined") return;
  const serialized = JSON.stringify(state);
  window.localStorage.setItem(CHAT_STATE_KEY, serialized);
  window.sessionStorage.setItem(CHAT_STATE_KEY, serialized);
}

export function loadChatState(): PersistedChatState | null {
  if (typeof window === "undefined") return null;
  const raw = readStorage(CHAT_STATE_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as PersistedChatState;
  } catch {
    return null;
  }
}

export function clearChatState() {
  if (typeof window === "undefined") return;
  window.localStorage.removeItem(CHAT_STATE_KEY);
  window.sessionStorage.removeItem(CHAT_STATE_KEY);
}

export function saveUserProfile(profile: UserProfile) {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(PROFILE_KEY, JSON.stringify(profile));
  window.localStorage.setItem("profile", JSON.stringify(profile));
  window.dispatchEvent(new CustomEvent("severity-profile-updated", { detail: profile }));
}

export function loadUserProfile(): UserProfile {
  if (typeof window === "undefined") return DEFAULT_PROFILE;
  const raw = window.localStorage.getItem(PROFILE_KEY) ?? window.localStorage.getItem("profile");
  if (!raw) return DEFAULT_PROFILE;
  try {
    return { ...DEFAULT_PROFILE, ...(JSON.parse(raw) as UserProfile) };
  } catch {
    return DEFAULT_PROFILE;
  }
}

export function getOrCreateUserId(): string {
  if (typeof window === "undefined") {
    return "anonymous-user";
  }

  const existing = window.localStorage.getItem(USER_ID_KEY);
  if (existing) {
    return existing;
  }

  const nextUserId = typeof crypto !== "undefined" && "randomUUID" in crypto ? crypto.randomUUID() : `user-${Date.now()}`;
  window.localStorage.setItem(USER_ID_KEY, nextUserId);
  return nextUserId;
}
