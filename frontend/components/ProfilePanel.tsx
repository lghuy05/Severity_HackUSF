import { FileText, Send, Shield } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

type ProfilePanelProps = {
  onSend: () => void;
  sent: boolean;
};

const PROFILE = {
  name: "Maya Rodriguez",
  age: 34,
  insurance: "Blue Shield PPO",
  language: "English / Spanish",
  allergies: "Penicillin",
};

export function ProfilePanel({ onSend, sent }: ProfilePanelProps) {
  return (
    <Card className="animate-fade-in">
      <CardHeader className="border-b border-white/[0.08] pb-4">
        <div className="flex items-center justify-between gap-4">
          <div>
            <p className="text-xs uppercase tracking-[0.24em] text-slate-500">Profile handoff</p>
            <CardTitle className="mt-1 text-xl">Share context with hospital</CardTitle>
            <CardDescription className="mt-2">
              The final step prepares a concise intake summary, profile, and language preference.
            </CardDescription>
          </div>
          <Badge variant={sent ? "safe" : "default"}>{sent ? "Sent" : "Ready"}</Badge>
        </div>
      </CardHeader>
      <CardContent className="grid gap-5 pt-6 md:grid-cols-[1fr,0.9fr]">
        <div className="space-y-3 rounded-[24px] border border-white/10 bg-white/[0.04] p-5">
          <div className="flex items-center gap-2 text-sm font-medium text-white">
            <Shield className="h-4 w-4 text-emerald-300" />
            Patient details
          </div>
          <div className="grid gap-3 text-sm text-slate-300 sm:grid-cols-2">
            <div>
              <p className="text-xs uppercase tracking-[0.18em] text-slate-500">Name</p>
              <p className="mt-1 text-white">{PROFILE.name}</p>
            </div>
            <div>
              <p className="text-xs uppercase tracking-[0.18em] text-slate-500">Age</p>
              <p className="mt-1 text-white">{PROFILE.age}</p>
            </div>
            <div>
              <p className="text-xs uppercase tracking-[0.18em] text-slate-500">Insurance</p>
              <p className="mt-1 text-white">{PROFILE.insurance}</p>
            </div>
            <div>
              <p className="text-xs uppercase tracking-[0.18em] text-slate-500">Language</p>
              <p className="mt-1 text-white">{PROFILE.language}</p>
            </div>
            <div className="sm:col-span-2">
              <p className="text-xs uppercase tracking-[0.18em] text-slate-500">Allergies</p>
              <p className="mt-1 text-white">{PROFILE.allergies}</p>
            </div>
          </div>
        </div>

        <div className="space-y-4 rounded-[24px] border border-white/10 bg-[#11192a]/85 p-5">
          <div className="flex items-center gap-2 text-sm font-medium text-white">
            <FileText className="h-4 w-4 text-sky-300" />
            Hospital summary packet
          </div>
          <p className="text-sm leading-7 text-slate-300">
            Includes current symptoms, translated summary, triage note, selected facility, and contact preference.
          </p>
          <Button onClick={onSend} disabled={sent} className="w-full gap-2">
            <Send className="h-4 w-4" />
            {sent ? "Sent to hospital" : "Send to hospital"}
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
