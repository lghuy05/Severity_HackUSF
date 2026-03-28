from agents.core.base_agent import create_agent
from shared.schemas import EmergencyOutput, LanguageOutput, NavigationOutput, SummaryOutput, TriageOutput


def build_summary(
    original_text: str,
    location: str,
    language_output: LanguageOutput,
    triage: TriageOutput,
    navigation: NavigationOutput,
    emergency: EmergencyOutput,
) -> SummaryOutput:
    return SummaryOutput(
        patient_input=original_text,
        location=location,
        detected_language=language_output.detected_language,
        normalized_text=language_output.translated_text,
        risk_level=triage.risk_level,
        triage_explanation=triage.explanation,
        recommended_sites=[hospital.name for hospital in navigation.hospitals],
        emergency_flag=emergency.emergency_flag,
        emergency_instructions=emergency.instructions,
    )


def _summary_handler(message, _context) -> SummaryOutput:
    payload = message if isinstance(message, dict) else {}
    return build_summary(
        original_text=str(payload["original_text"]),
        location=str(payload["location"]),
        language_output=payload["language_output"],
        triage=payload["triage"],
        navigation=payload["navigation"],
        emergency=payload["emergency"],
    )


summary_agent = create_agent(
    key="summary",
    name="summary_agent",
    instruction=(
        "Return a structured JSON summary of the case. "
        "Include normalized symptoms, risk level, recommended care sites, and emergency actions."
    ),
    handler=_summary_handler,
    metadata={"role": "structured_summary"},
)
