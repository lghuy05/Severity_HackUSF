import type { AnalyzeResponse, SummaryOutput } from "../../shared/types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export async function analyzeSymptoms(payload: { text: string; location: string }): Promise<AnalyzeResponse> {
  const response = await fetch(`${API_BASE_URL}/analyze`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    throw new Error("Analyze request failed");
  }

  return response.json();
}

export async function communicateSummary(summary: SummaryOutput): Promise<{ message: string }> {
  const response = await fetch(`${API_BASE_URL}/communicate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ summary }),
  });

  if (!response.ok) {
    throw new Error("Communicate request failed");
  }

  return response.json();
}
