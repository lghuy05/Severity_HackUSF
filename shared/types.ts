export type RiskLevel = "low" | "medium" | "high";

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
  language_output: LanguageOutput;
  triage: TriageOutput;
  navigation: NavigationOutput;
  summary: SummaryOutput;
  provider_message: string;
  emergency_flag: boolean;
  emergency: EmergencyOutput;
};

export type ChatMessage = {
  id: string;
  role: "user" | "assistant";
  content: string;
};

export type AgentStep = {
  key: string;
  label: string;
  status: "idle" | "running" | "done";
  detail?: string;
};
