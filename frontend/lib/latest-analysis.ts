"use client";

import type { AnalyzeResponse } from "@shared/types";

const ANALYSIS_KEY = "heb.latest.analysis";
const CONTEXT_KEY = "heb.latest.context";

export type LatestContext = {
  text: string;
  location: string;
};

export function saveLatestAnalysis(analysis: AnalyzeResponse) {
  if (typeof window === "undefined") {
    return;
  }

  window.sessionStorage.setItem(ANALYSIS_KEY, JSON.stringify(analysis));
}

export function loadLatestAnalysis(): AnalyzeResponse | null {
  if (typeof window === "undefined") {
    return null;
  }

  const raw = window.sessionStorage.getItem(ANALYSIS_KEY);
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

  window.sessionStorage.setItem(CONTEXT_KEY, JSON.stringify(context));
}

export function loadLatestContext(): LatestContext | null {
  if (typeof window === "undefined") {
    return null;
  }

  const raw = window.sessionStorage.getItem(CONTEXT_KEY);
  if (!raw) {
    return null;
  }

  try {
    return JSON.parse(raw) as LatestContext;
  } catch {
    return null;
  }
}
