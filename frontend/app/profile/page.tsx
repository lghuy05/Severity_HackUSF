"use client";

import { useEffect, useState } from "react";
import { Loader2, Save, ShieldCheck, UserRound } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { getUserProfile, updateUserProfile } from "@/lib/api";
import { getAppCopy } from "@/lib/app-copy";
import { LANGUAGE_OPTIONS } from "@/lib/i18n";
import { DEFAULT_PROFILE, loadUserProfile } from "@/lib/session-store";
import { useUiLanguage } from "@/lib/use-ui-language";
import type { UserProfile } from "@shared/types";

export default function ProfilePage() {
  const language = useUiLanguage();
  const copy = getAppCopy(language).profile;
  const [profile, setProfile] = useState<UserProfile>(DEFAULT_PROFILE);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    setProfile(loadUserProfile());

    async function loadProfile() {
      try {
        const nextProfile = await getUserProfile();
        setProfile(nextProfile);
        setSaved(true);
        setError("");
      } catch {
        setError("Profile service is unavailable. Showing the locally cached profile.");
      } finally {
        setIsLoading(false);
      }
    }

    void loadProfile();
  }, []);

  function updateField<K extends keyof UserProfile>(key: K, value: UserProfile[K]) {
    setSaved(false);
    setError("");
    setProfile((current) => ({ ...current, [key]: value }));
  }

  async function save() {
    setIsSaving(true);
    try {
      const nextProfile = await updateUserProfile(profile);
      setProfile(nextProfile);
      setSaved(true);
      setError("");
    } catch {
      setError("Unable to save your profile right now.");
      setSaved(false);
    } finally {
      setIsSaving(false);
    }
  }

  return (
    <main className="app-shell-gradient min-h-screen">
      <div className="mx-auto max-w-5xl px-4 pb-16 pt-10 sm:px-6 lg:px-8">
        <Badge>{copy.badge}</Badge>
        <div className="mt-5 max-w-2xl">
          <h1 className="text-4xl font-semibold tracking-[-0.04em] text-slate-950 sm:text-5xl">{copy.title}</h1>
          <p className="mt-4 text-base leading-8 text-slate-600">{copy.description}</p>
        </div>

        <div className="mt-10 grid gap-6 lg:grid-cols-[minmax(0,1.1fr)_360px]">
          <Card>
            <CardHeader className="border-b border-slate-200 pb-4">
              <div className="flex items-center justify-between gap-4">
                <div>
                  <CardTitle className="flex items-center gap-2">
                    <UserRound className="h-5 w-5 text-sky-500" />
                    {copy.defaultsTitle}
                  </CardTitle>
                  <CardDescription className="mt-2">{copy.defaultsDescription}</CardDescription>
                </div>
                <Badge variant={saved ? "safe" : "default"}>{isLoading ? copy.statusLoading : saved ? copy.statusSaved : copy.statusEditing}</Badge>
              </div>
            </CardHeader>
            <CardContent className="grid gap-4 pt-6 sm:grid-cols-2">
              <label className="block sm:col-span-2">
                <span className="mb-2 block text-xs uppercase tracking-[0.18em] text-slate-500">{copy.name}</span>
                <input
                  value={profile.name}
                  onChange={(event) => updateField("name", event.target.value)}
                  className="h-12 w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 text-sm text-slate-900 outline-none"
                />
              </label>

              <label className="block">
                <span className="mb-2 block text-xs uppercase tracking-[0.18em] text-slate-500">{copy.preferredLanguage}</span>
                <select
                  value={profile.language}
                  onChange={(event) => updateField("language", event.target.value)}
                  className="h-12 w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 text-sm text-slate-900 outline-none"
                >
                  {LANGUAGE_OPTIONS.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </label>

              <label className="block">
                <span className="mb-2 block text-xs uppercase tracking-[0.18em] text-slate-500">{copy.defaultLocation}</span>
                <input
                  value={profile.location}
                  onChange={(event) => updateField("location", event.target.value)}
                  className="h-12 w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 text-sm text-slate-900 outline-none"
                />
              </label>

              <label className="block">
                <span className="mb-2 block text-xs uppercase tracking-[0.18em] text-slate-500">{copy.age}</span>
                <input
                  value={profile.age ?? ""}
                  onChange={(event) => updateField("age", event.target.value ? Number(event.target.value) : null)}
                  className="h-12 w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 text-sm text-slate-900 outline-none"
                />
              </label>

              <label className="block">
                <span className="mb-2 block text-xs uppercase tracking-[0.18em] text-slate-500">{copy.gender}</span>
                <select
                  value={profile.gender ?? ""}
                  onChange={(event) => updateField("gender", event.target.value || null)}
                  className="h-12 w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 text-sm text-slate-900 outline-none"
                >
                  <option value="">Prefer not to say</option>
                  <option value="female">Female</option>
                  <option value="male">Male</option>
                  <option value="non-binary">Non-binary</option>
                  <option value="other">Other</option>
                </select>
              </label>

              <div className="sm:col-span-2">
                <Button onClick={() => void save()} className="gap-2" disabled={isLoading || isSaving}>
                  {isSaving ? <Loader2 className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />}
                  {isSaving ? copy.saving : copy.saveProfile}
                </Button>
                {error ? <p className="mt-3 text-sm text-rose-600">{error}</p> : null}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="border-b border-slate-200 pb-4">
              <CardTitle className="flex items-center gap-2">
                <ShieldCheck className="h-5 w-5 text-emerald-500" />
                {copy.contextTitle}
              </CardTitle>
              <CardDescription className="mt-2">{copy.contextDescription}</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4 pt-6 text-sm leading-7 text-slate-600">
              <p><span className="text-slate-400">Name:</span> {profile.name || "User"}</p>
              <p><span className="text-slate-400">Language:</span> {profile.language || "en"}</p>
              <p><span className="text-slate-400">Location:</span> {profile.location || copy.notSet}</p>
              <p><span className="text-slate-400">Age:</span> {profile.age ?? copy.notSet}</p>
              <p><span className="text-slate-400">Gender:</span> {profile.gender ?? copy.notSet}</p>
            </CardContent>
          </Card>
        </div>
      </div>
    </main>
  );
}
