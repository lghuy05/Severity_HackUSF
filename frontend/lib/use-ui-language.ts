"use client";

import { useEffect, useState } from "react";

import { DEFAULT_PROFILE, loadUserProfile } from "@/lib/session-store";
import { LANGUAGE_OPTIONS, type UiLanguage } from "@/lib/i18n";

const SUPPORTED_LANGUAGES = new Set<UiLanguage>(LANGUAGE_OPTIONS.map((option) => option.value));

function normalizeLanguage(value: string | null | undefined): UiLanguage {
  if (value && SUPPORTED_LANGUAGES.has(value as UiLanguage)) {
    return value as UiLanguage;
  }
  return "en";
}

export function useUiLanguage(): UiLanguage {
  const [language, setLanguage] = useState<UiLanguage>(normalizeLanguage(DEFAULT_PROFILE.language));

  useEffect(() => {
    const sync = () => {
      setLanguage(normalizeLanguage(loadUserProfile().language));
    };

    sync();
    window.addEventListener("storage", sync);
    window.addEventListener("severity-profile-updated", sync as EventListener);

    return () => {
      window.removeEventListener("storage", sync);
      window.removeEventListener("severity-profile-updated", sync as EventListener);
    };
  }, []);

  return language;
}
