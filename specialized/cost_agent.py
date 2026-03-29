from __future__ import annotations

from agents.message_types import A2AEnvelope
from backend.schemas import AgentMessage
from core.base_agent import BaseADKAgent
from tools.cost_tool import compare_care_costs


class CostAgent(BaseADKAgent):
    def __init__(self) -> None:
        super().__init__(
            key="cost_agent",
            instruction=(
                "Compare likely healthcare costs for the current care options. "
                "Use structured, approximate estimates suitable for patient navigation."
            ),
            tools={"cost_tool": compare_care_costs},
        )

    def process(self, message: AgentMessage, envelope: A2AEnvelope) -> AgentMessage:
        message.cost_options = self.call_tool("cost_tool", message)
        return message
