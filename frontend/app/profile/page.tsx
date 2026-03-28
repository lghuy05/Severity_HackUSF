"use client";

import { useState } from "react";
import { PencilLine, Save, ShieldCheck } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

type ProfileState = {
  name: string;
  age: string;
  insurance: string;
  language: string;
  allergies: string;
  phone: string;
};

const INITIAL_PROFILE: ProfileState = {
  name: "Maya Rodriguez",
  age: "34",
  insurance: "Blue Shield PPO",
  language: "English / Spanish",
  allergies: "Penicillin",
  phone: "(415) 555-0189",
};

export default function ProfilePage() {
  const [profile, setProfile] = useState(INITIAL_PROFILE);
  const [saved, setSaved] = useState(false);

  function updateField(key: keyof ProfileState, value: string) {
    setSaved(false);
    setProfile((current) => ({ ...current, [key]: value }));
  }

  return (
    <main className="relative min-h-screen overflow-hidden bg-[#0b0f14] text-white">
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_left,rgba(56,189,248,0.14),transparent_24%),radial-gradient(circle_at_80%_10%,rgba(129,140,248,0.14),transparent_20%),linear-gradient(180deg,#0b0f14_0%,#0d1320_100%)]" />
      <div className="relative z-10 mx-auto max-w-5xl px-4 pb-10 pt-24 sm:px-6 lg:px-8">
        <Badge>Profile</Badge>
        <div className="mt-5 max-w-2xl">
          <h1 className="text-4xl font-semibold tracking-[-0.04em] sm:text-5xl">Editable patient profile</h1>
          <p className="mt-4 text-base leading-8 text-slate-300">
            This is a mock profile page for now. It keeps the same quiet product feel and can later connect to persisted user data.
          </p>
        </div>

        <div className="mt-10 grid gap-6 lg:grid-cols-[minmax(0,1.1fr)_360px]">
          <Card>
            <CardHeader className="border-b border-white/[0.08] pb-4">
              <div className="flex items-center justify-between gap-4">
                <div>
                  <CardTitle className="flex items-center gap-2">
                    <PencilLine className="h-5 w-5 text-sky-300" />
                    Patient details
                  </CardTitle>
                  <CardDescription className="mt-2">Edit the mock fields below. No backend persistence yet.</CardDescription>
                </div>
                <Badge variant={saved ? "safe" : "default"}>{saved ? "Saved locally" : "Editing"}</Badge>
              </div>
            </CardHeader>
            <CardContent className="grid gap-4 pt-6 sm:grid-cols-2">
              {(
                [
                  ["name", "Full name"],
                  ["age", "Age"],
                  ["insurance", "Insurance"],
                  ["language", "Preferred language"],
                  ["allergies", "Allergies"],
                  ["phone", "Phone"],
                ] as const
              ).map(([key, label]) => (
                <label key={key} className="block">
                  <span className="mb-2 block text-xs uppercase tracking-[0.18em] text-slate-500">{label}</span>
                  <input
                    value={profile[key]}
                    onChange={(event) => updateField(key, event.target.value)}
                    className="h-12 w-full rounded-2xl border border-white/[0.10] bg-white/[0.04] px-4 text-sm text-white outline-none transition placeholder:text-slate-500 focus:border-sky-300/[0.35] focus:bg-white/[0.06]"
                  />
                </label>
              ))}
              <div className="sm:col-span-2">
                <Button onClick={() => setSaved(true)} className="gap-2">
                  <Save className="h-4 w-4" />
                  Save changes
                </Button>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="border-b border-white/[0.08] pb-4">
              <CardTitle className="flex items-center gap-2">
                <ShieldCheck className="h-5 w-5 text-emerald-300" />
                Handoff preview
              </CardTitle>
              <CardDescription className="mt-2">What would travel with the user when contacting a hospital.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4 pt-6 text-sm leading-7 text-slate-300">
              <p><span className="text-slate-500">Name:</span> {profile.name}</p>
              <p><span className="text-slate-500">Insurance:</span> {profile.insurance}</p>
              <p><span className="text-slate-500">Language:</span> {profile.language}</p>
              <p><span className="text-slate-500">Allergies:</span> {profile.allergies}</p>
              <p><span className="text-slate-500">Phone:</span> {profile.phone}</p>
            </CardContent>
          </Card>
        </div>
      </div>
    </main>
  );
}
