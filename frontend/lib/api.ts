import type {
  AnalyzeResponse,
  ChatIntent,
  ChatSessionState,
  ChatStreamChunk,
  ChatTurnResponse,
  SummaryOutput,
  UserProfile,
  VisitAssistantUserProfile,
  VisitExtractNoteResponse,
  VisitSavedNote,
  VisitScheduleResponse,
  VisitStructuredNote,
  VisitSummarizeResponse,
  VisitTranslateTurnResponse,
} from "../../shared/types";
import { DEFAULT_PROFILE, getOrCreateUserId, loadUserProfile, saveUserProfile } from "./session-store";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

type RequestOptions = Omit<RequestInit, "headers"> & {
  headers?: HeadersInit;
  includeProfileInBody?: boolean;
  profile?: UserProfile | null;
};

type ProfilePatch = Partial<UserProfile>;

function withUserHeaders(headers?: HeadersInit): Headers {
  const nextHeaders = new Headers(headers);
  nextHeaders.set("x-user-id", getOrCreateUserId());
  return nextHeaders;
}

function withOptionalProfileBody(body: unknown, profile?: UserProfile | null): BodyInit | undefined {
  if (body == null) {
    return undefined;
  }

  if (typeof body === "string") {
    try {
      return JSON.stringify({
        ...(JSON.parse(body) as Record<string, unknown>),
        profile: profile ?? loadUserProfile(),
      });
    } catch {
      return body;
    }
  }

  return JSON.stringify({
    ...(body as Record<string, unknown>),
    profile: profile ?? loadUserProfile(),
  });
}

async function apiFetch(path: string, options: RequestOptions = {}): Promise<Response> {
  const { includeProfileInBody = false, profile = null, body, headers, ...rest } = options;
  const nextHeaders = withUserHeaders(headers);

  if (body != null && !nextHeaders.has("Content-Type")) {
    nextHeaders.set("Content-Type", "application/json");
  }

  return fetch(`${API_BASE_URL}${path}`, {
    ...rest,
    headers: nextHeaders,
    body: includeProfileInBody ? withOptionalProfileBody(body, profile) : (body as BodyInit | undefined),
  });
}

export async function analyzeSymptoms(payload: { text: string; location: string }): Promise<AnalyzeResponse> {
  const response = await apiFetch("/analyze", {
    method: "POST",
    includeProfileInBody: true,
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    throw new Error("Analyze request failed");
  }

  return response.json();
}

export async function communicateSummary(summary: SummaryOutput): Promise<{ message: string }> {
  const response = await apiFetch("/communicate", {
    method: "POST",
    includeProfileInBody: true,
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
    session?: ChatSessionState | null;
    profile?: UserProfile | null;
  },
  onChunk: (chunk: ChatStreamChunk) => void,
): Promise<ChatTurnResponse> {
  const response = await apiFetch("/chat/stream", {
    method: "POST",
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
  const response = await apiFetch(`/chat/session/${sessionId}`);
  if (!response.ok) {
    throw new Error("Fetch chat session failed");
  }
  return response.json();
}

export async function extractVisitNote(transcript: string): Promise<VisitExtractNoteResponse> {
  const response = await apiFetch("/visit/extract-note", {
    method: "POST",
    includeProfileInBody: true,
    body: JSON.stringify({ transcript }),
  });

  if (!response.ok) {
    throw new Error("Visit note extraction failed");
  }

  return response.json();
}

export async function summarizeVisitConversation(transcript: string): Promise<VisitSummarizeResponse> {
  const response = await apiFetch("/visit/summarize", {
    method: "POST",
    includeProfileInBody: true,
    body: JSON.stringify({ transcript }),
  });

  if (!response.ok) {
    throw new Error("Visit summary generation failed");
  }

  return response.json();
}

export async function translateVisitTurn(payload: {
  text: string;
  source_language: string;
  target_language: string;
}): Promise<VisitTranslateTurnResponse> {
  const response = await apiFetch("/visit/translate-turn", {
    method: "POST",
    includeProfileInBody: true,
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    throw new Error("Visit translation failed");
  }

  return response.json();
}

export async function scheduleVisitAppointment(
  note: VisitStructuredNote,
  userProfile: VisitAssistantUserProfile,
): Promise<VisitScheduleResponse> {
  const cachedProfile = loadUserProfile();
  const response = await apiFetch("/visit/schedule", {
    method: "POST",
    includeProfileInBody: true,
    profile: {
      ...DEFAULT_PROFILE,
      ...cachedProfile,
      language: userProfile.language || cachedProfile.language,
      location: userProfile.location || cachedProfile.location,
      age: userProfile.age ?? cachedProfile.age ?? null,
      gender: userProfile.gender ?? cachedProfile.gender ?? null,
    },
    body: JSON.stringify({ note, user_profile: userProfile }),
  });

  if (!response.ok) {
    throw new Error("Visit scheduling failed");
  }

  return response.json();
}

export async function getUserProfile(): Promise<UserProfile> {
  const response = await apiFetch("/user/profile");
  if (!response.ok) {
    throw new Error("Fetch user profile failed");
  }

  const profile = { ...DEFAULT_PROFILE, ...(await response.json() as UserProfile) };
  saveUserProfile(profile);
  return profile;
}

export async function updateUserProfile(patch: ProfilePatch): Promise<UserProfile> {
  const response = await apiFetch("/user/profile", {
    method: "POST",
    body: JSON.stringify(patch),
  });
  if (!response.ok) {
    throw new Error("Update user profile failed");
  }

  const profile = { ...DEFAULT_PROFILE, ...(await response.json() as UserProfile) };
  saveUserProfile(profile);
  return profile;
}

export async function listVisitNotes(): Promise<VisitSavedNote[]> {
  const response = await apiFetch("/visit/notes");
  if (!response.ok) {
    throw new Error("Fetch visit notes failed");
  }

  const payload = await response.json() as { notes: VisitSavedNote[] };
  return payload.notes;
}

export async function saveVisitNote(payload: {
  title: string;
  transcript: string;
  summary: string;
  structured_note: VisitStructuredNote;
}): Promise<VisitSavedNote> {
  const response = await apiFetch("/visit/notes", {
    method: "POST",
    includeProfileInBody: true,
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    throw new Error("Save visit note failed");
  }

  return response.json();
}
