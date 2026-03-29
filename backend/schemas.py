from __future__ import annotations

from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field


RiskLevel = Literal["low", "medium", "high"]
ChatIntent = Literal["symptoms", "guidance", "care", "cost"]
SemanticIntent = Literal["symptom_check", "guidance", "seek_care", "cost", "emergency", "unclear"]
SemanticSeverity = Literal["mild", "moderate", "severe", "unknown"]


class UserProfile(BaseModel):
    language: str = "en"
    location: str = ""
    age: int | None = None
    gender: str | None = None


class AssistantState(BaseModel):
    symptom: str | None = None
    severity: str | None = None
    risk: str | None = None
    stage: str = "intake"
    intent: str | None = None
    missing_fields: list[str] = Field(default_factory=list)


class SemanticMeaning(BaseModel):
    intent: SemanticIntent = "unclear"
    symptoms: list[str] = Field(default_factory=list)
    severity: SemanticSeverity = "unknown"
    urgency: RiskLevel = "low"
    user_goal: Literal["get_advice", "find_hospital", "compare_cost", "unclear"] = "unclear"
    has_enough_info: bool = False
    answered_pending_question: bool = False
    resolved_field: Literal["severity", "duration", "breathing", "symptom", "other"] | None = None
    resolved_value: str | None = None
    follow_up_needed: bool = False
    follow_up_question: str | None = None
    follow_up_kind: Literal["yes_no", "multiple_choice", "free_text"] = "free_text"
    follow_up_options: list[str] = Field(default_factory=list)
    is_new_case: bool = False


class FollowUpQuestion(BaseModel):
    question_id: str
    text: str
    kind: Literal["yes_no", "multiple_choice", "free_text"]
    options: list[str] = Field(default_factory=list)
    expected_field: Literal["severity", "duration", "breathing", "symptom", "other"] = "other"


class SessionMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class AnalyzeRequest(BaseModel):
    text: str = Field(min_length=1)
    location: str = Field(min_length=1)
    user_id: str | None = None
    preferred_language: str | None = None


class ChatSessionState(BaseModel):
    session_id: str | None = None
    request_id: str | None = None
    user_id: str | None = None
    location: str
    preferred_language: str | None = None
    raw_text: str | None = None
    normalized_text: str | None = None
    detected_language: str | None = None
    translated_text: str | None = None
    risk_level: RiskLevel | None = None
    risk_reason: str | None = None
    hospitals: list["HospitalLocation"] = Field(default_factory=list)
    cost_options: list["CostOption"] = Field(default_factory=list)
    provider_summary: str | None = None
    emergency_flag: bool = False
    emergency_instructions: list[str] = Field(default_factory=list)
    consent_to_fetch_external: bool = False
    profile: UserProfile = Field(default_factory=UserProfile)
    state: AssistantState = Field(default_factory=AssistantState)
    pending_question: FollowUpQuestion | None = None
    follow_up_answers: dict[str, str] = Field(default_factory=dict)
    messages: list[SessionMessage] = Field(default_factory=list)
    conversation_summary: str = ""


class QuickAction(BaseModel):
    label: str
    intent: ChatIntent
    prompt: str | None = None


class AssistantTurnPayload(BaseModel):
    message: str = ""
    follow_up: FollowUpQuestion | None = None
    actions: list[QuickAction] = Field(default_factory=list)
    ui_blocks: list[Literal["guidance", "care_options", "costs", "emergency"]] = Field(default_factory=list)


class ChatTurnRequest(BaseModel):
    session_id: str | None = None
    intent: ChatIntent
    message: str | None = None
    location: str = Field(min_length=1)
    preferred_language: str | None = None
    user_id: str | None = None
    session: ChatSessionState | None = None
    profile: UserProfile | None = None


class ChatTurnResponse(BaseModel):
    session_id: str
    request_id: str
    intent: ChatIntent
    session: ChatSessionState
    state: AssistantState
    assistant_message: str = ""
    ui_blocks: list[Literal["guidance", "care_options", "costs", "emergency"]] = Field(default_factory=list)
    suggested_actions: list[QuickAction] = Field(default_factory=list)
    follow_up_question: FollowUpQuestion | None = None
    response: AssistantTurnPayload = Field(default_factory=AssistantTurnPayload)
    trace: list["TraceEvent"] = Field(default_factory=list)
    agent_flow: list["AgentFlowStep"] = Field(default_factory=list)


class ChatStreamChunk(BaseModel):
    type: Literal["message", "state", "done"]
    session_id: str
    request_id: str
    intent: ChatIntent
    message: str | None = None
    session: ChatSessionState | None = None
    ui_blocks: list[Literal["guidance", "care_options", "costs", "emergency"]] = Field(default_factory=list)
    suggested_actions: list[QuickAction] = Field(default_factory=list)
    follow_up_question: FollowUpQuestion | None = None
    response: AssistantTurnPayload = Field(default_factory=AssistantTurnPayload)
    trace: list["TraceEvent"] = Field(default_factory=list)
    agent_flow: list["AgentFlowStep"] = Field(default_factory=list)


class HospitalLocation(BaseModel):
    name: str
    address: str
    lat: float
    lng: float
    phone: str
    open_now: bool = True
    google_maps_uri: str | None = None


class CostOption(BaseModel):
    provider: str
    care_type: str
    estimated_cost: str
    notes: str
    estimated_wait: str | None = None
    coverage_summary: str | None = None
    source: str | None = None


class LanguageOutput(BaseModel):
    detected_language: str = "en"
    simplified_text: str = ""
    translated_text: str = ""


class TriageOutput(BaseModel):
    risk_level: RiskLevel = "low"
    explanation: str = ""


class NavigationOutput(BaseModel):
    origin: str
    recommendation: str
    hospitals: list[HospitalLocation] = Field(default_factory=list)


class EmergencyOutput(BaseModel):
    emergency_flag: bool = False
    instructions: list[str] = Field(default_factory=list)


class SummaryOutput(BaseModel):
    patient_input: str
    location: str
    detected_language: str
    normalized_text: str
    risk_level: RiskLevel
    triage_explanation: str
    recommended_sites: list[str] = Field(default_factory=list)
    emergency_flag: bool = False
    emergency_instructions: list[str] = Field(default_factory=list)


class TraceEvent(BaseModel):
    event: str
    request_id: str
    agent: str | None = None
    next_agent: str | None = None
    intent: str | None = None
    tool: str | None = None
    latency_ms: int | None = None
    detail: str | None = None
    error: str | None = None
    state_fields: list[str] = Field(default_factory=list)


class AgentFlowStep(BaseModel):
    agent: str
    label: str
    status: Literal["pending", "running", "done"]
    summary: str
    tools: list[str] = Field(default_factory=list)


class AgentMessage(BaseModel):
    request_id: str = Field(default_factory=lambda: str(uuid4()))
    user_id: str | None = None
    location: str
    raw_text: str
    preferred_language: str | None = None
    normalized_text: str | None = None
    detected_language: str | None = None
    translated_text: str | None = None
    risk_level: RiskLevel | None = None
    risk_reason: str | None = None
    hospitals: list[HospitalLocation] = Field(default_factory=list)
    cost_options: list[CostOption] = Field(default_factory=list)
    provider_summary: str | None = None
    emergency_flag: bool = False
    emergency_instructions: list[str] = Field(default_factory=list)
    trace: list[TraceEvent] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    def visible_fields(self) -> list[str]:
        return sorted(
            key
            for key, value in self.model_dump().items()
            if value not in (None, [], {}, "")
            and key not in {"trace", "metadata"}
        )


class AnalyzeResponse(BaseModel):
    request_id: str
    language_output: LanguageOutput
    triage: TriageOutput
    navigation: NavigationOutput
    summary: SummaryOutput
    provider_message: str
    emergency_flag: bool
    emergency: EmergencyOutput
    cost_options: list[CostOption] = Field(default_factory=list)
    agent_flow: list[AgentFlowStep] = Field(default_factory=list)
    trace: list[TraceEvent] = Field(default_factory=list)


class CommunicationRequest(BaseModel):
    summary: SummaryOutput


class CommunicationResponse(BaseModel):
    message: str
