import asyncio
from datetime import datetime, timezone
from typing import Any, AsyncGenerator

import httpx

from agents.communication_agent import format_provider_message
from agents.emergency_agent import emergency_response
from agents.language_agent import process_language
from agents.navigation_agent import find_nearby_hospitals
from agents.summary_agent import build_summary
from agents.triage_agent import triage_symptoms
from backend.memory import get_emergency_context
from shared.schemas import AnalyzeRequest, AnalyzeResponse, CommunicationResponse


async def stream_mock_orchestrator(
    session_id: str,
    user_message: str,
    history: list[dict[str, str]],
) -> AsyncGenerator[dict[str, Any], None]:
    # Simulate an async multi-agent workflow so the frontend can render live updates.
    _ = (session_id, user_message, history)

    lowered = user_message.lower()
    emergency_keywords = ("call 911", "help", "heart attack", "can't breathe", "cant breathe")
    if any(keyword in lowered for keyword in emergency_keywords):
        yield {
            "status": "critical",
            "agent": "Triage Agent",
            "message": "Critical severity detected. Escalating to Emergency Agent.",
        }

        emergency_context = get_emergency_context(session_id=session_id, limit=5)

        yield {
            "status": "action",
            "agent": "Emergency Agent",
            "message": "Compiling emergency payload and contacting dispatch...",
        }

        dispatch_payload = {
            "session_id": session_id,
            "extracted_symptoms": emergency_context,
            "urgency_level": "CRITICAL",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                await client.post(
                    "http://localhost:8000/api/emergency/dispatch",
                    json=dispatch_payload,
                )
        except httpx.HTTPError:
            pass

        yield {
            "type": "final",
            "severity": "CRITICAL",
            "response": "Emergency services have been notified.",
            "emergency_dispatched": True,
        }
        return

    yield {
        "type": "status",
        "agent": "system",
        "message": "Agent received message",
    }
    await asyncio.sleep(0.8)

    yield {
        "type": "status",
        "agent": "triage",
        "message": "Evaluating severity...",
    }
    await asyncio.sleep(0.9)

    yield {
        "type": "status",
        "agent": "navigation",
        "message": "Fetching nearby clinics...",
    }
    await asyncio.sleep(0.9)

    if any(keyword in lowered for keyword in ("chest pain", "can't breathe", "cant breathe", "unconscious")):
        severity = "HIGH"
        response = "This may be an emergency. Call 911 now or go to the nearest ER immediately."
        map_trigger = True
    elif any(keyword in lowered for keyword in ("fever", "dizzy", "headache", "pain")):
        severity = "MEDIUM"
        response = "Please visit an urgent care clinic today for in-person evaluation."
        map_trigger = True
    else:
        severity = "LOW"
        response = "Monitor symptoms, rest, and follow up with primary care if symptoms worsen."
        map_trigger = False

    yield {
        "type": "final",
        "severity": severity,
        "response": response,
        "map_trigger": map_trigger,
    }


def run_analysis(request: AnalyzeRequest) -> AnalyzeResponse:
    language_output = process_language(request.text)
    triage = triage_symptoms(language_output.simplified_text)
    navigation = find_nearby_hospitals(triage.risk_level, request.location)
    emergency = emergency_response(triage.risk_level)
    summary = build_summary(
        original_text=request.text,
        location=request.location,
        language_output=language_output,
        triage=triage,
        navigation=navigation,
        emergency=emergency,
    )
    provider_message = format_provider_message(summary)

    return AnalyzeResponse(
        language_output=language_output,
        triage=triage,
        navigation=navigation,
        summary=summary,
        provider_message=provider_message.message,
        emergency_flag=emergency.emergency_flag,
        emergency=emergency,
    )


def run_communication(summary) -> CommunicationResponse:
    return format_provider_message(summary)
