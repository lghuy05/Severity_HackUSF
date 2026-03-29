from __future__ import annotations

import json
import os
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from backend.schemas import AgentMessage, AssistantState, FollowUpQuestion, SemanticMeaning


GEMINI_ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"


class GeminiToolError(RuntimeError):
    pass


def _extract_text(payload: dict[str, Any]) -> str:
    candidates = payload.get("candidates", [])
    if not candidates:
        raise GeminiToolError("Gemini returned no candidates")

    content = candidates[0].get("content", {})
    parts = content.get("parts", [])
    text_parts = [part.get("text", "") for part in parts if part.get("text")]
    if not text_parts:
        raise GeminiToolError("Gemini returned no text parts")
    return "".join(text_parts)


def generate_structured_json(
    *,
    prompt: str,
    schema: dict[str, Any],
    model: str | None = None,
    tools: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise GeminiToolError("GEMINI_API_KEY is not configured")

    model_name = model or os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    endpoint = f"{GEMINI_ENDPOINT.format(model=model_name)}?{urlencode({'key': api_key})}"
    body: dict[str, Any] = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "responseMimeType": "application/json",
            "responseJsonSchema": schema,
            "temperature": 0.2,
        },
    }
    if tools:
        body["tools"] = tools

    request = Request(
        endpoint,
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urlopen(request, timeout=25) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:  # pragma: no cover - depends on remote service
        detail = exc.read().decode("utf-8", errors="ignore")
        raise GeminiToolError(f"Gemini HTTP error {exc.code}: {detail}") from exc
    except TimeoutError as exc:  # pragma: no cover - depends on network
        raise GeminiToolError("Gemini network timeout") from exc
    except URLError as exc:  # pragma: no cover - depends on network
        raise GeminiToolError(f"Gemini network error: {exc}") from exc

    return json.loads(_extract_text(payload))


def normalize_language_with_gemini(message: AgentMessage) -> dict[str, Any]:
    return generate_structured_json(
        prompt=(
            "You are a healthcare language normalization agent. "
            "Detect the user's language, simplify the wording without losing symptoms, "
            "and translate to concise clinical English if needed.\n\n"
            f"User text: {message.raw_text}\n"
            f"Preferred language: {message.preferred_language or 'unknown'}"
        ),
        schema={
            "type": "object",
            "properties": {
                "detected_language": {"type": "string"},
                "simplified_text": {"type": "string"},
                "translated_text": {"type": "string"},
            },
            "required": ["detected_language", "simplified_text", "translated_text"],
        },
    )


def assess_triage_with_gemini(message: AgentMessage) -> dict[str, Any]:
    return generate_structured_json(
        prompt=(
            "You are a healthcare triage agent for a patient navigation workflow. "
            "Assess urgency conservatively. Return high if symptoms could indicate an emergency, "
            "especially chest pain, neurological deficits, trouble breathing, severe bleeding, or fainting. "
            "This is not a diagnosis.\n\n"
            f"Normalized text: {message.translated_text or message.normalized_text or message.raw_text}\n"
            f"Location: {message.location}"
        ),
        schema={
            "type": "object",
            "properties": {
                "risk_level": {
                    "type": "string",
                    "enum": ["low", "medium", "high"],
                },
                "risk_reason": {"type": "string"},
            },
            "required": ["risk_level", "risk_reason"],
        },
    )


def draft_provider_summary_with_gemini(message: AgentMessage) -> dict[str, Any]:
    hospitals = [
        {
            "name": hospital.name,
            "address": hospital.address,
            "phone": hospital.phone,
        }
        for hospital in message.hospitals
    ]
    costs = [
        {
            "provider": item.provider,
            "care_type": item.care_type,
            "estimated_cost": item.estimated_cost,
        }
        for item in message.cost_options
    ]

    return generate_structured_json(
        prompt=(
            "Write a concise provider-facing intake summary for a healthcare navigation system. "
            "Use plain professional language and keep it factual.\n\n"
            f"Patient text: {message.raw_text}\n"
            f"Normalized text: {message.translated_text or message.normalized_text or message.raw_text}\n"
            f"Risk level: {message.risk_level}\n"
            f"Risk reason: {message.risk_reason}\n"
            f"Location: {message.location}\n"
            f"Emergency flag: {message.emergency_flag}\n"
            f"Hospitals: {json.dumps(hospitals)}\n"
            f"Costs: {json.dumps(costs)}"
        ),
        schema={
            "type": "object",
            "properties": {
                "provider_summary": {"type": "string"},
            },
            "required": ["provider_summary"],
        },
    )


def estimate_costs_with_gemini(message: AgentMessage) -> dict[str, Any]:
    hospitals = [
        {
            "name": hospital.name,
            "address": hospital.address,
            "open_now": hospital.open_now,
        }
        for hospital in message.hospitals[:5]
    ]

    return generate_structured_json(
        prompt=(
            "You are a U.S. healthcare cost navigation agent. "
            "Estimate approximate visit costs, likely wait times, and a brief insurance or self-pay note for each facility. "
            "Do not claim exact billing data. Use realistic U.S. ranges based on facility type, urgency, and location. "
            "Return concise patient-facing guidance.\n\n"
            f"Location: {message.location}\n"
            f"Risk level: {message.risk_level}\n"
            f"Symptoms: {message.translated_text or message.normalized_text or message.raw_text}\n"
            f"Facilities: {json.dumps(hospitals)}"
        ),
        schema={
            "type": "object",
            "properties": {
                "cost_options": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "provider": {"type": "string"},
                            "care_type": {"type": "string"},
                            "estimated_cost": {"type": "string"},
                            "estimated_wait": {"type": "string"},
                            "coverage_summary": {"type": "string"},
                            "notes": {"type": "string"},
                            "source": {"type": "string"},
                        },
                        "required": [
                            "provider",
                            "care_type",
                            "estimated_cost",
                            "estimated_wait",
                            "coverage_summary",
                            "notes",
                            "source",
                        ],
                    },
                }
            },
            "required": ["cost_options"],
        },
    )


def translate_text_items(*, texts: list[str], target_language: str) -> list[str]:
    if not texts:
        return []
    if target_language.lower().startswith("en"):
        return texts

    payload = generate_structured_json(
        prompt=(
            "Translate the following user-facing healthcare assistant messages into the requested language. "
            "Keep the meaning, preserve urgency, and use natural plain language. "
            "Return translations in the same order.\n\n"
            f"Target language: {target_language}\n"
            f"Texts: {json.dumps(texts)}"
        ),
        schema={
            "type": "object",
            "properties": {
                "translations": {
                    "type": "array",
                    "items": {"type": "string"},
                }
            },
            "required": ["translations"],
        },
    )
    translations = payload.get("translations", [])
    if not isinstance(translations, list) or len(translations) != len(texts):
        raise GeminiToolError("Gemini returned invalid translations")
    return [str(item) for item in translations]


def summarize_appointment_reason(chat_history: str) -> str:
    payload = generate_structured_json(
        prompt=(
            "You are a medical assistant. Based on the following conversation between a patient and a healthcare assistant,\n"
            "write a single concise sentence (max 20 words) summarizing the medical reason why this patient needs to see a doctor.\n"
            "Do not copy the conversation directly. Summarize it as a reason for a medical appointment.\n"
            "Only return the summary sentence, nothing else.\n\n"
            f"Conversation:\n{chat_history}"
        ),
        schema={
            "type": "object",
            "properties": {
                "summary": {"type": "string"},
            },
            "required": ["summary"],
        },
    )
    summary = str(payload.get("summary", "")).strip()
    if not summary:
        raise GeminiToolError("Gemini returned empty appointment summary")
    return summary


def extract_structured_meaning(
    message: str,
    state: AssistantState,
    conversation_summary: str = "",
    pending_question: FollowUpQuestion | None = None,
    follow_up_answers: dict[str, str] | None = None,
    recent_turns: list[dict[str, str]] | None = None,
    profile: dict[str, Any] | None = None,
) -> SemanticMeaning:
    recent_turns = recent_turns or []
    profile = profile or {}
    payload = generate_structured_json(
        prompt=(
            "You are the semantic understanding layer for a healthcare chat assistant. "
            "Interpret the latest user message in context of the current structured state. "
            "Use the rolling summary for older context and the recent turns for conversational continuity. "
            "Do not treat the full conversation transcript as available; use only the context provided. "
            "Do not rely on literal keyword matching. Infer likely symptom severity from natural language such as "
            "'5/10 pain', 'kinda bad', or 'feels worse now'. "
            "If a pending follow-up question exists, first decide whether the latest user message answers that question. "
            "Prioritize resolving the pending question before doing anything else. "
            "Use the pending question text and expected field as the main interpretation target. "
            "If the answer is sufficient, set answered_pending_question=true, set follow_up_needed=false, "
            "and fill resolved_field and resolved_value as well as any structured fields like severity. "
            "If you still need a follow-up question, also return which structured field it is asking about in follow_up_field. "
            "Always set follow_up_field when follow_up_needed=true. "
            "If the current state already contains a symptom, do not ask for the symptom again. "
            "If the current state already contains severity, do not ask for severity again unless the user explicitly says it changed. "
            "Do not ask the same question again unless the answer is still insufficient. "
            "For severity follow-ups, interpret numeric scales naturally: "
            "1-3/10 is usually mild, 4-6/10 is moderate, and 7-10/10 is severe. "
            "Also interpret vague phrases like 'kinda bad' as moderate and 'much worse' as severe. "
            "Only mark follow_up_needed when the system genuinely needs one more detail. "
            "Do not block explicit user goals like finding care or comparing costs.\n\n"
            f"Latest user message: {message}\n"
            f"Current state: {state.model_dump(mode='json')}\n"
            f"Profile: {json.dumps(profile)}\n"
            f"Pending follow-up: {pending_question.model_dump(mode='json') if pending_question else 'None'}\n"
            f"Previous follow-up answers: {json.dumps(follow_up_answers or {})}\n"
            f"Conversation summary: {conversation_summary or 'None'}\n"
            f"Recent turns: {json.dumps(recent_turns)}"
        ),
        schema={
            "type": "object",
            "properties": {
                "intent": {
                    "type": "string",
                    "enum": ["symptom_check", "guidance", "seek_care", "cost", "emergency", "unclear"],
                },
                "symptoms": {"type": "array", "items": {"type": "string"}},
                "severity": {
                    "type": "string",
                    "enum": ["mild", "moderate", "severe", "unknown"],
                },
                "urgency": {
                    "type": "string",
                    "enum": ["low", "medium", "high"],
                },
                "user_goal": {
                    "type": "string",
                    "enum": ["get_advice", "find_hospital", "compare_cost", "unclear"],
                },
                "has_enough_info": {"type": "boolean"},
                "answered_pending_question": {"type": "boolean"},
                "resolved_field": {
                    "type": ["string", "null"],
                    "enum": ["severity", "duration", "breathing", "symptom", "other", None],
                },
                "resolved_value": {"type": ["string", "null"]},
                "follow_up_needed": {"type": "boolean"},
                "follow_up_field": {
                    "type": ["string", "null"],
                    "enum": ["severity", "duration", "breathing", "symptom", "other", None],
                },
                "follow_up_question": {"type": ["string", "null"]},
                "follow_up_kind": {
                    "type": "string",
                    "enum": ["yes_no", "multiple_choice", "free_text"],
                },
                "follow_up_options": {
                    "type": "array",
                    "items": {"type": "string"},
                },
                "is_new_case": {"type": "boolean"},
            },
            "required": [
                "intent",
                "symptoms",
                "severity",
                "urgency",
                "user_goal",
                "has_enough_info",
                "answered_pending_question",
                "resolved_field",
                "resolved_value",
                "follow_up_needed",
                "follow_up_field",
                "follow_up_question",
                "follow_up_kind",
                "follow_up_options",
                "is_new_case",
            ],
        },
    )
    return SemanticMeaning(**payload)


def generate_assistant_reply(
    *,
    latest_message: str,
    state: AssistantState,
    meaning: SemanticMeaning,
    risk_reason: str | None,
    hospitals: list[dict[str, Any]] | None = None,
    cost_options: list[dict[str, Any]] | None = None,
    emergency_instructions: list[str] | None = None,
    follow_up_question: str | None = None,
    recent_turns: list[dict[str, str]] | None = None,
    conversation_summary: str = "",
    profile: dict[str, Any] | None = None,
    target_language: str = "en",
) -> str:
    hospitals = hospitals or []
    cost_options = cost_options or []
    emergency_instructions = emergency_instructions or []
    recent_turns = recent_turns or []
    profile = profile or {}

    payload = generate_structured_json(
        prompt=(
            "You are a calm, supportive healthcare assistant. "
            "Write exactly one short conversational reply for the user. "
            "Sound natural, human, warm, and direct, like a strong ChatGPT-style assistant. "
            "Use the structured state and semantic meaning as the source of truth. "
            "Use the recent turns and rolling summary only to maintain continuity and avoid sounding repetitive. "
            "Do not use labels such as 'Understanding', 'Risk', or 'Next step'. "
            "Do not expose internal system terms, risk classes, or reasoning labels unless urgency is truly high. "
            "Avoid stiff clinical phrasing unless the situation is truly urgent. "
            "Be gently reassuring when appropriate, but stay medically careful. "
            "Use welcoming wording that feels supportive, not bureaucratic. "
            "Translate urgency into natural language. For example: "
            "low urgency -> 'this doesn't look urgent right now', "
            "medium urgency -> 'this is worth getting checked soon', "
            "high urgency -> 'this could be urgent and you should get care now'. "
            "If follow_up_question is present, weave it naturally into the same reply instead of sounding like a form. "
            "If the user asked for care, acknowledge that directly and briefly. "
            "If the user asked about cost, acknowledge that directly and briefly. "
            "Do not repeat obvious information from the user's last message unless needed for clarity. "
            "Reply entirely in the requested target language. "
            "Do not write more than 2 short paragraphs and keep the reply under 80 words.\n\n"
            f"Latest user message: {latest_message}\n"
            f"Target language: {target_language}\n"
            f"Profile: {json.dumps(profile)}\n"
            f"State: {state.model_dump(mode='json')}\n"
            f"Meaning: {meaning.model_dump(mode='json')}\n"
            f"Conversation summary: {conversation_summary or 'None'}\n"
            f"Recent turns: {json.dumps(recent_turns)}\n"
            f"Risk reason: {risk_reason or ''}\n"
            f"Hospitals: {json.dumps(hospitals)}\n"
            f"Cost options: {json.dumps(cost_options)}\n"
            f"Emergency instructions: {json.dumps(emergency_instructions)}\n"
            f"Follow-up question: {follow_up_question or ''}"
        ),
        schema={
            "type": "object",
            "properties": {
                "message": {"type": "string"},
            },
            "required": ["message"],
        },
    )
    return str(payload["message"]).strip()
