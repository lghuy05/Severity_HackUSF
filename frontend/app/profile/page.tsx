"use client";

import { useEffect, useState } from "react";
import { Save, ShieldCheck, UserRound } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { DEFAULT_PROFILE, loadUserProfile, saveUserProfile } from "@/lib/session-store";
import type { UserProfile } from "@shared/types";

export default function ProfilePage() {
  const [profile, setProfile] = useState<UserProfile>(DEFAULT_PROFILE);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    setProfile(loadUserProfile());
  }, []);

  function updateField<K extends keyof UserProfile>(key: K, value: UserProfile[K]) {
    setSaved(false);
    setProfile((current) => ({ ...current, [key]: value }));
  }

  function save() {
    saveUserProfile(profile);
    setSaved(true);
  }

  return (
    <main className="app-shell-gradient min-h-screen">
      <div className="mx-auto max-w-5xl px-4 pb-16 pt-10 sm:px-6 lg:px-8">
        <Badge>Profile</Badge>
        <div className="mt-5 max-w-2xl">
          <h1 className="text-4xl font-semibold tracking-[-0.04em] text-slate-950 sm:text-5xl">Personal settings</h1>
          <p className="mt-4 text-base leading-8 text-slate-600">
            These details are stored locally and automatically used for future conversations.
          </p>
        </div>

        <div className="mt-10 grid gap-6 lg:grid-cols-[minmax(0,1.1fr)_360px]">
          <Card>
            <CardHeader className="border-b border-slate-200 pb-4">
              <div className="flex items-center justify-between gap-4">
                <div>
                  <CardTitle className="flex items-center gap-2">
                    <UserRound className="h-5 w-5 text-sky-500" />
                    Assistant defaults
                  </CardTitle>
                  <CardDescription className="mt-2">Language and location are applied automatically to every new request.</CardDescription>
                </div>
                <Badge variant={saved ? "safe" : "default"}>{saved ? "Saved" : "Editing"}</Badge>
              </div>
            </CardHeader>
            <CardContent className="grid gap-4 pt-6 sm:grid-cols-2">
              <label className="block">
                <span className="mb-2 block text-xs uppercase tracking-[0.18em] text-slate-500">Preferred language</span>
                <select
                  value={profile.language}
                  onChange={(event) => updateField("language", event.target.value)}
                  className="h-12 w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 text-sm text-slate-900 outline-none"
                >
                  <option value="en">English</option>
                  <option value="es">Español</option>
                  <option value="fr">Français</option>
                  <option value="pt">Português</option>
                  <option value="vi">Tiếng Việt</option>
                  <option value="zh">中文</option>
                </select>
              </label>

              <label className="block">
                <span className="mb-2 block text-xs uppercase tracking-[0.18em] text-slate-500">Default location</span>
                <input
                  value={profile.location}
                  onChange={(event) => updateField("location", event.target.value)}
                  className="h-12 w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 text-sm text-slate-900 outline-none"
                />
              </label>

              <label className="block">
                <span className="mb-2 block text-xs uppercase tracking-[0.18em] text-slate-500">Age (optional)</span>
                <input
                  value={profile.age ?? ""}
                  onChange={(event) => updateField("age", event.target.value ? Number(event.target.value) : null)}
                  className="h-12 w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 text-sm text-slate-900 outline-none"
                />
              </label>

              <label className="block">
                <span className="mb-2 block text-xs uppercase tracking-[0.18em] text-slate-500">Gender (optional)</span>
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
                <Button onClick={save} className="gap-2">
                  <Save className="h-4 w-4" />
                  Save profile
                </Button>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="border-b border-slate-200 pb-4">
              <CardTitle className="flex items-center gap-2">
                <ShieldCheck className="h-5 w-5 text-emerald-500" />
                Assistant context
              </CardTitle>
              <CardDescription className="mt-2">This profile is applied automatically before the assistant decides what to ask or do next.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4 pt-6 text-sm leading-7 text-slate-600">
              <p><span className="text-slate-400">Language:</span> {profile.language || "en"}</p>
              <p><span className="text-slate-400">Location:</span> {profile.location || "Not set"}</p>
              <p><span className="text-slate-400">Age:</span> {profile.age ?? "Not set"}</p>
              <p><span className="text-slate-400">Gender:</span> {profile.gender ?? "Not set"}</p>
            </CardContent>
          </Card>
        </div>
      </div>
    </main>
  );
}
