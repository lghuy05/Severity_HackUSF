from __future__ import annotations

import json
import os
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from tools.gemini_tool import GeminiToolError, generate_structured_json

from backend.visit_assistant.schemas import (
    VisitExtractNoteResponse,
    VisitScheduleRequest,
    VisitScheduleResponse,
    VisitSummarizeResponse,
    VisitTranslateTurnResponse,
    VisitStructuredNote,
)


class VisitAssistantError(RuntimeError):
    pass


class VisitAssistantConfigError(VisitAssistantError):
    pass


EXTRACT_NOTE_SCHEMA = {
    "type": "object",
    "properties": {
        "summary": {"type": "string"},
        "symptoms": {"type": "array", "items": {"type": "string"}},
        "severity": {"type": "string", "enum": ["low", "medium", "high", "unknown"]},
        "timeline": {"type": "string"},
        "action_items": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["summary", "symptoms", "severity", "timeline", "action_items"],
}

SUMMARY_SCHEMA = {
    "type": "object",
    "properties": {
        "summary": {"type": "string"},
    },
    "required": ["summary"],
}

TRANSLATE_TURN_SCHEMA = {
    "type": "object",
    "properties": {
        "translated_text": {"type": "string"},
    },
    "required": ["translated_text"],
}


def _normalize_transcript(transcript: str) -> str:
    cleaned = transcript.strip()
    if not cleaned:
        raise VisitAssistantError("Transcript is required")
    return cleaned


def extract_note(transcript: str) -> VisitExtractNoteResponse:
    cleaned = _normalize_transcript(transcript)
    payload = generate_structured_json(
        prompt=(
            "You are a medical visit assistant. Extract a concise, clinically useful visit note "
            "from the transcript. Do not invent facts. Keep the summary readable for a human. "
            "Symptoms should be short phrases. Timeline should describe onset and progression if present, "
            "otherwise say 'Not clearly stated'. Action items should list explicit next steps, self-care, "
            "tests, follow-ups, or scheduling needs. Severity reflects overall urgency in the transcript.\n\n"
            f"Transcript:\n{cleaned}"
        ),
        schema=EXTRACT_NOTE_SCHEMA,
    )
    return VisitExtractNoteResponse(note=VisitStructuredNote(**payload))


def summarize_conversation(transcript: str) -> VisitSummarizeResponse:
    cleaned = _normalize_transcript(transcript)
    payload = generate_structured_json(
        prompt=(
            "You are a medical documentation specialist. Rewrite the transcript into a clean, "
            "human-readable visit summary in 1-2 short paragraphs. Preserve only medically relevant "
            "details, symptoms, severity cues, timeline, and next steps. Remove filler and repetition. "
            "Do not diagnose beyond what is explicitly stated.\n\n"
            f"Transcript:\n{cleaned}"
        ),
        schema=SUMMARY_SCHEMA,
    )
    return VisitSummarizeResponse(summary=payload["summary"].strip())


def translate_turn(*, text: str, source_language: str, target_language: str) -> VisitTranslateTurnResponse:
    cleaned = _normalize_transcript(text)
    payload = generate_structured_json(
        prompt=(
            "You are a real-time medical conversation interpreter. Translate the source utterance into the target language. "
            "Preserve meaning, tone, and clinically relevant details. Do not add explanations. "
            "Return only the translated utterance.\n\n"
            f"Source language: {source_language}\n"
            f"Target language: {target_language}\n"
            f"Utterance:\n{cleaned}"
        ),
        schema=TRANSLATE_TURN_SCHEMA,
    )
    return VisitTranslateTurnResponse(
        source_text=cleaned,
        translated_text=payload["translated_text"].strip(),
        source_language=source_language,
        target_language=target_language,
    )


def schedule_appointment(request: VisitScheduleRequest) -> VisitScheduleResponse:
    api_key = os.getenv("VAPI_PRIVATE_KEY")
    assistant_id = os.getenv("VISIT_ASSISTANT_VAPI_ASSISTANT_ID") or os.getenv("VAPI_ASSISTANT_ID")
    phone_number_id = os.getenv("VISIT_ASSISTANT_VAPI_PHONE_NUMBER_ID") or os.getenv("VAPI_PHONE_NUMBER_ID")
    endpoint = os.getenv("VISIT_ASSISTANT_VAPI_URL", "https://api.vapi.ai/call")

    if not api_key:
        raise VisitAssistantConfigError("VAPI_PRIVATE_KEY is not configured")
    if not assistant_id:
        raise VisitAssistantConfigError("VISIT_ASSISTANT_VAPI_ASSISTANT_ID or VAPI_ASSISTANT_ID is not configured")
    if not phone_number_id:
        raise VisitAssistantConfigError("VISIT_ASSISTANT_VAPI_PHONE_NUMBER_ID or VAPI_PHONE_NUMBER_ID is not configured")
    if not request.user_profile.phone_number.strip():
        raise VisitAssistantError("A phone number is required to schedule an appointment")

    customer_number = request.user_profile.phone_number.strip()
    if not customer_number.startswith("+"):
        customer_number = f"+1{customer_number}"

    outbound_payload = {
        "assistantId": assistant_id,
        "phoneNumberId": phone_number_id,
        "customer": {
            "number": customer_number,
        },
        "assistantOverrides": {
            "variableValues": {
                "patient": {
                    "fullName": request.user_profile.full_name.strip(),
                    "location": request.user_profile.location,
                    "language": request.user_profile.language,
                    "age": request.user_profile.age,
                    "gender": request.user_profile.gender,
                },
                "visitNote": request.note.model_dump(),
            }
        },
    }

    http_request = Request(
        endpoint,
        data=json.dumps(outbound_payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urlopen(http_request, timeout=25) as response:
            raw_response = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="ignore")
        raise VisitAssistantError(f"VAPI HTTP error {exc.code}: {detail}") from exc
    except TimeoutError as exc:
        raise VisitAssistantError("VAPI network timeout") from exc
    except URLError as exc:
        raise VisitAssistantError(f"VAPI network error: {exc}") from exc

    external_call_id = (
        raw_response.get("id")
        or raw_response.get("call", {}).get("id")
        or raw_response.get("callId")
    )

    return VisitScheduleResponse(
        status="scheduled" if external_call_id else "queued",
        provider="vapi",
        message="Appointment scheduling request sent to VAPI.",
        external_call_id=external_call_id,
        request_payload=outbound_payload,
        raw_response=raw_response,
    )
