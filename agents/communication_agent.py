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
