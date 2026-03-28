import { FolderClock, Sparkles } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

export default function RecordsPage() {
  return (
    <main className="relative min-h-screen overflow-hidden bg-[#0b0f14] text-white">
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_top,rgba(56,189,248,0.12),transparent_22%),radial-gradient(circle_at_84%_12%,rgba(129,140,248,0.12),transparent_18%),linear-gradient(180deg,#0b0f14_0%,#0d1320_100%)]" />
      <div className="relative z-10 mx-auto max-w-5xl px-4 pb-10 pt-24 sm:px-6 lg:px-8">
        <Badge>Past Records</Badge>
        <div className="mt-5 max-w-2xl">
          <h1 className="text-4xl font-semibold tracking-[-0.04em] sm:text-5xl">Past records will live here</h1>
          <p className="mt-4 text-base leading-8 text-slate-300">
            Keeping this intentionally empty for now. Later this page can show previous conversations, referrals, and sent summaries.
          </p>
        </div>

        <Card className="mt-10">
          <CardHeader className="border-b border-white/[0.08] pb-4">
            <CardTitle className="flex items-center gap-2">
              <FolderClock className="h-5 w-5 text-violet-300" />
              No records yet
            </CardTitle>
            <CardDescription className="mt-2">This page is ready as a placeholder route.</CardDescription>
          </CardHeader>
          <CardContent className="flex min-h-[280px] flex-col items-center justify-center gap-4 pt-6 text-center">
            <div className="flex h-16 w-16 items-center justify-center rounded-[22px] border border-white/[0.10] bg-white/[0.04]">
              <Sparkles className="h-7 w-7 text-sky-300" />
            </div>
            <div>
              <p className="text-lg font-medium text-white">Nothing to show yet</p>
              <p className="mt-2 max-w-md text-sm leading-7 text-slate-400">
                Once record history is added, this page can show prior symptom sessions, hospital comparisons, and profile handoffs.
              </p>
            </div>
          </CardContent>
        </Card>
      </div>
    </main>
  );
}
