from __future__ import annotations

from agents.message_types import A2AEnvelope
from backend.schemas import AgentMessage
from core.base_agent import BaseADKAgent


class EmergencyAgent(BaseADKAgent):
    def __init__(self) -> None:
        super().__init__(
            key="emergency_agent",
            instruction=(
                "Provide direct emergency guidance for high-risk symptoms. "
                "Focus on safety, immediate action, and avoiding delay."
            ),
        )

    def process(self, message: AgentMessage, envelope: A2AEnvelope) -> AgentMessage:
        if message.risk_level == "high":
            message.emergency_flag = True
            message.emergency_instructions = [
                "Call 911 immediately if the chest pain is severe, worsening, or associated with shortness of breath.",
                "Do not drive yourself if you feel faint, confused, or unsafe to travel.",
                "Go to the nearest emergency department now.",
            ]
        else:
            message.emergency_flag = False
            message.emergency_instructions = ["No emergency escalation required based on the current triage result."]
        return message
