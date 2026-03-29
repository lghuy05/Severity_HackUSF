import type { AnalyzeResponse, ChatIntent, ChatSessionState, ChatStreamChunk, ChatTurnResponse, SummaryOutput, UserProfile } from "../../shared/types";

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

export async function streamChatTurn(
  payload: {
    intent: ChatIntent;
    session_id?: string;
    message?: string;
    location: string;
    preferred_language?: string;
    profile?: UserProfile | null;
  },
  onChunk: (chunk: ChatStreamChunk) => void,
): Promise<ChatTurnResponse> {
  const response = await fetch(`${API_BASE_URL}/chat/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (!response.ok || !response.body) {
    throw new Error("Chat stream request failed");
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let finalChunk: ChatStreamChunk | null = null;
  let assistantMessage = "";

  while (true) {
    const { value, done } = await reader.read();
    if (done) {
      break;
    }

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop() ?? "";

    for (const line of lines) {
      if (!line.trim()) {
        continue;
      }
      const chunk = JSON.parse(line) as ChatStreamChunk;
      onChunk(chunk);
      if (chunk.type === "message" && chunk.message) {
        assistantMessage = chunk.message;
      }
      if (chunk.type === "done") {
        finalChunk = chunk;
      }
    }
  }

  if (!finalChunk?.session) {
    throw new Error("Chat stream completed without final state");
  }

  return {
    request_id: finalChunk.request_id,
    intent: finalChunk.intent,
    session: finalChunk.session,
    state: finalChunk.session.state,
    session_id: finalChunk.session_id,
    assistant_message: assistantMessage,
    ui_blocks: finalChunk.ui_blocks,
    suggested_actions: finalChunk.suggested_actions,
    follow_up_question: finalChunk.follow_up_question,
    response: finalChunk.response,
    trace: finalChunk.trace,
    agent_flow: finalChunk.agent_flow,
  };
}

export async function getChatSession(sessionId: string): Promise<ChatSessionState> {
  const response = await fetch(`${API_BASE_URL}/chat/session/${sessionId}`);
  if (!response.ok) {
    throw new Error("Fetch chat session failed");
  }
  return response.json();
}
