from __future__ import annotations

from backend.schemas import AgentMessage


def format_provider_message(message: AgentMessage) -> str:
    hospital_names = ", ".join(hospital.name for hospital in message.hospitals) or "No sites selected"
    costs = "; ".join(f"{item.provider}: {item.estimated_cost}" for item in message.cost_options) or "Cost estimates unavailable"
    emergency_note = (
        "Emergency escalation triggered. "
        if message.emergency_flag
        else "No emergency escalation triggered. "
    )
    return (
        f"Patient reported: {message.raw_text}. "
        f"Normalized concern: {message.translated_text or message.normalized_text or message.raw_text}. "
        f"Risk level: {message.risk_level}. "
        f"Reason: {message.risk_reason}. "
        f"Location: {message.location}. "
        f"{emergency_note}"
        f"Recommended facilities: {hospital_names}. "
        f"Estimated costs: {costs}."
    )
