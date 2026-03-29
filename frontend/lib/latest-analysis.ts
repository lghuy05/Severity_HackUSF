"use client";

import type { AnalyzeResponse } from "@shared/types";

const ANALYSIS_KEY = "heb.latest.analysis";
const CONTEXT_KEY = "heb.latest.context";

function readStorage(key: string) {
  if (typeof window === "undefined") {
    return null;
  }

  return window.localStorage.getItem(key) ?? window.sessionStorage.getItem(key);
}

export type LatestContext = {
  text: string;
  location: string;
};

export function saveLatestAnalysis(analysis: AnalyzeResponse) {
  if (typeof window === "undefined") {
    return;
  }

  const serialized = JSON.stringify(analysis);
  window.localStorage.setItem(ANALYSIS_KEY, serialized);
  window.sessionStorage.setItem(ANALYSIS_KEY, serialized);
}

export function loadLatestAnalysis(): AnalyzeResponse | null {
  if (typeof window === "undefined") {
    return null;
  }

  const raw = readStorage(ANALYSIS_KEY);
  if (!raw) {
    return null;
  }

  try {
    return JSON.parse(raw) as AnalyzeResponse;
  } catch {
    return null;
  }
}

export function saveLatestContext(context: LatestContext) {
  if (typeof window === "undefined") {
    return;
  }

  const serialized = JSON.stringify(context);
  window.localStorage.setItem(CONTEXT_KEY, serialized);
  window.sessionStorage.setItem(CONTEXT_KEY, serialized);
}

export function loadLatestContext(): LatestContext | null {
  if (typeof window === "undefined") {
    return null;
  }

  const raw = readStorage(CONTEXT_KEY);
  if (!raw) {
    return null;
  }

  try {
    return JSON.parse(raw) as LatestContext;
  } catch {
    return null;
  }
}

export function clearLatestAnalysis() {
  if (typeof window === "undefined") {
    return;
  }

  window.localStorage.removeItem(ANALYSIS_KEY);
  window.sessionStorage.removeItem(ANALYSIS_KEY);
}

export function clearLatestContext() {
  if (typeof window === "undefined") {
    return;
  }

  window.localStorage.removeItem(CONTEXT_KEY);
  window.sessionStorage.removeItem(CONTEXT_KEY);
}
