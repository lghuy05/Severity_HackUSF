from agents.communication_agent import format_provider_message
from agents.emergency_agent import emergency_response
from agents.language_agent import process_language
from agents.navigation_agent import find_nearby_hospitals
from agents.summary_agent import build_summary
from agents.triage_agent import triage_symptoms
from shared.schemas import AnalyzeRequest, AnalyzeResponse, CommunicationResponse


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
