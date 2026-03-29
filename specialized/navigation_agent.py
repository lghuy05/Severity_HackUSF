from __future__ import annotations

from agents.message_types import A2AEnvelope
from backend.schemas import AgentMessage
from core.base_agent import BaseADKAgent
from tools.maps_tool import find_nearby_services


class NavigationAgent(BaseADKAgent):
    def __init__(self) -> None:
        super().__init__(
            key="navigation_agent",
            instruction=(
                "Find nearby hospitals or clinics appropriate for the user's risk level and location. "
                "For high-risk situations, prioritize emergency departments."
            ),
            tools={"maps_tool": find_nearby_services},
        )

    def process(self, message: AgentMessage, envelope: A2AEnvelope) -> AgentMessage:
        message.hospitals = self.call_tool("maps_tool", message)
        return message
