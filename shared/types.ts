export type RiskLevel = "low" | "medium" | "high";
export type ChatIntent = "symptoms" | "guidance" | "care" | "cost";
export type SemanticIntent = "symptom_check" | "guidance" | "seek_care" | "cost" | "emergency" | "unclear";
export type SemanticSeverity = "mild" | "moderate" | "severe" | "unknown";
export type UserProfile = {
  language: string;
  location: string;
  age?: number | null;
  gender?: string | null;
};

export type AssistantState = {
  symptom: string | null;
  severity: string | null;
  risk: string | null;
  stage: string;
  intent: string | null;
  missing_fields: string[];
};

export type SemanticMeaning = {
  intent: SemanticIntent;
  symptoms: string[];
  severity: SemanticSeverity;
  urgency: RiskLevel;
  user_goal: "get_advice" | "find_hospital" | "compare_cost" | "unclear";
  has_enough_info: boolean;
  answered_pending_question: boolean;
  resolved_field?: "severity" | "duration" | "breathing" | "symptom" | "other" | null;
  resolved_value?: string | null;
  follow_up_needed: boolean;
  follow_up_question?: string | null;
  follow_up_kind: "yes_no" | "multiple_choice" | "free_text";
  follow_up_options: string[];
  is_new_case: boolean;
};

export type FollowUpQuestion = {
  question_id: string;
  text: string;
  kind: "yes_no" | "multiple_choice" | "free_text";
  options: string[];
  expected_field: "severity" | "duration" | "breathing" | "symptom" | "other";
};

export type SessionMessage = {
  role: "user" | "assistant";
  content: string;
};

export type LanguageOutput = {
  detected_language: string;
  simplified_text: string;
  translated_text: string;
};

export type TriageOutput = {
  risk_level: RiskLevel;
  explanation: string;
};

export type HospitalLocation = {
  name: string;
  address: string;
  lat: number;
  lng: number;
  phone: string;
  open_now: boolean;
  google_maps_uri?: string | null;
};

export type CostOption = {
  provider: string;
  care_type: string;
  estimated_cost: string;
  notes: string;
  estimated_wait?: string | null;
  coverage_summary?: string | null;
  source?: string | null;
};

export type NavigationOutput = {
  origin: string;
  recommendation: string;
  hospitals: HospitalLocation[];
};

export type EmergencyOutput = {
  emergency_flag: boolean;
  instructions: string[];
};

export type SummaryOutput = {
  patient_input: string;
  location: string;
  detected_language: string;
  normalized_text: string;
  risk_level: RiskLevel;
  triage_explanation: string;
  recommended_sites: string[];
  emergency_flag: boolean;
  emergency_instructions: string[];
};

export type AnalyzeResponse = {
  request_id: string;
  language_output: LanguageOutput;
  triage: TriageOutput;
  navigation: NavigationOutput;
  summary: SummaryOutput;
  provider_message: string;
  emergency_flag: boolean;
  emergency: EmergencyOutput;
  cost_options: CostOption[];
  agent_flow: AgentStep[];
  trace: TraceEvent[];
};

export type ChatSessionState = {
  session_id?: string | null;
  request_id?: string | null;
  user_id?: string | null;
  location: string;
  preferred_language?: string | null;
  raw_text?: string | null;
  normalized_text?: string | null;
  detected_language?: string | null;
  translated_text?: string | null;
  risk_level?: RiskLevel | null;
  risk_reason?: string | null;
  hospitals: HospitalLocation[];
  cost_options: CostOption[];
  provider_summary?: string | null;
  emergency_flag: boolean;
  emergency_instructions: string[];
  consent_to_fetch_external: boolean;
  profile: UserProfile;
  state: AssistantState;
  pending_question?: FollowUpQuestion | null;
  follow_up_answers: Record<string, string>;
  messages: SessionMessage[];
  conversation_summary: string;
};

export type QuickAction = {
  label: string;
  intent: ChatIntent;
  prompt?: string | null;
};

export type AssistantTurnPayload = {
  message: string;
  follow_up?: FollowUpQuestion | null;
  actions: QuickAction[];
  ui_blocks: Array<"guidance" | "care_options" | "costs" | "emergency">;
};

export type ChatTurnResponse = {
  session_id: string;
  request_id: string;
  intent: ChatIntent;
  session: ChatSessionState;
  state: AssistantState;
  assistant_message: string;
  ui_blocks: Array<"guidance" | "care_options" | "costs" | "emergency">;
  suggested_actions: QuickAction[];
  follow_up_question?: FollowUpQuestion | null;
  response: AssistantTurnPayload;
  trace: TraceEvent[];
  agent_flow: AgentStep[];
};

export type ChatStreamChunk = {
  type: "message" | "state" | "done";
  session_id: string;
  request_id: string;
  intent: ChatIntent;
  message?: string | null;
  session?: ChatSessionState | null;
  ui_blocks: Array<"guidance" | "care_options" | "costs" | "emergency">;
  suggested_actions: QuickAction[];
  follow_up_question?: FollowUpQuestion | null;
  response: AssistantTurnPayload;
  trace: TraceEvent[];
  agent_flow: AgentStep[];
};

export type TraceEvent = {
  event: string;
  request_id: string;
  agent?: string;
  next_agent?: string;
  intent?: string;
  tool?: string;
  latency_ms?: number;
  detail?: string;
  error?: string;
  state_fields: string[];
};

export type ChatMessage = {
  id: string;
  role: "user" | "assistant";
  content: string;
};

export type AgentStep = {
  agent: string;
  label: string;
  status: "pending" | "running" | "done";
  summary: string;
  tools: string[];
};
