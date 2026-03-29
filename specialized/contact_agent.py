from __future__ import annotations

from agents.message_types import A2AEnvelope
from backend.schemas import AgentMessage
from core.base_agent import BaseADKAgent
from tools.gemini_tool import GeminiToolError, draft_provider_summary_with_gemini
from tools.message_formatter import format_provider_message


class ContactAgent(BaseADKAgent):
    def __init__(self) -> None:
        super().__init__(
            key="contact_agent",
            instruction=(
                "Create a structured provider handoff message summarizing symptoms, triage outcome, "
                "location, recommended facilities, and estimated cost context."
            ),
            tools={
                "provider_summary_llm_tool": draft_provider_summary_with_gemini,
                "message_formatter_tool": format_provider_message,
            },
        )

    def process(self, message: AgentMessage, envelope: A2AEnvelope) -> AgentMessage:
        try:
            llm_result = self.call_tool("provider_summary_llm_tool", message)
            message.provider_summary = str(llm_result["provider_summary"]).strip()
        except (GeminiToolError, KeyError, TypeError, ValueError):
            message.provider_summary = self.call_tool("message_formatter_tool", message)
        return message
