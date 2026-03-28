from typing import Any, AsyncGenerator

from agents.communication_agent import format_provider_message
from agents.emergency_agent import emergency_response
from agents.language_agent import process_language
from agents.navigation_agent import find_nearby_hospitals
from agents.summary_agent import build_summary
from agents.triage_agent import triage_symptoms
from backend.llm_agents import estimate_costs, run_triage, simplify_and_translate
from backend.maps import get_nearby_hospitals
from shared.schemas import AnalyzeRequest, AnalyzeResponse, CommunicationResponse


async def stream_mock_orchestrator(
    session_id: str,
    user_message: str,
    history: list[dict[str, str]],
    history_str: str,
    latitude: float | None = None,
    longitude: float | None = None,
    target_language: str = "en",
) -> AsyncGenerator[dict[str, Any], None]:
    _ = (session_id, history)

    yield {
        "status": "processing",
        "agent": "Triage Agent",
        "message": "Analyzing symptoms...",
    }

    triage = await run_triage(user_message=user_message, history=history_str)
    severity = triage.get("severity", "MEDIUM")
    reason = triage.get("reason", "No reason provided.")
    response_text = triage.get("response_text", "Please seek medical care if symptoms worsen.")

    yield {
        "status": "processing",
        "agent": "Pricing Agent",
        "message": "Estimating treatment costs...",
    }
    cost_data = await estimate_costs(reason)

    yield {
        "status": "processing",
        "agent": "Language Agent",
        "message": f"Translating and simplifying to {target_language}...",
    }
    translated_text = await simplify_and_translate(response_text, target_language)

    yield {
        "status": "processing",
        "agent": "Maps Agent",
        "message": "Checking location for nearby facilities...",
    }

    hospital_list: list[dict[str, Any]] = []
    if severity in ["HIGH", "CRITICAL"] and latitude is not None and longitude is not None:
        hospital_list = await get_nearby_hospitals(latitude, longitude)

    yield {
        "type": "final",
        "severity": severity,
        "reason": reason,
        "response": translated_text,
        "hospitals": hospital_list,
        "estimated_costs": cost_data,
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
