from agents.core.base_agent import create_agent
from shared.schemas import CommunicationResponse, SummaryOutput


def format_provider_message(summary: SummaryOutput) -> CommunicationResponse:
    message = (
        f"Patient reported: {summary.patient_input}. "
        f"Normalized concern: {summary.normalized_text}. "
        f"Risk level: {summary.risk_level}. "
        f"Location: {summary.location}. "
        f"Recommended sites: {', '.join(summary.recommended_sites)}."
    )
    return CommunicationResponse(message=message)


communication_agent = create_agent(
    key="communication",
    name="communication_agent",
    instruction=(
        "Format a concise provider-ready handoff from the case summary. "
        "Keep the message factual and easy for a clinician to scan."
    ),
    handler=lambda message, _context: format_provider_message(message),
    metadata={"role": "provider_handoff"},
)
