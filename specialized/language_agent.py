from __future__ import annotations

from agents.message_types import A2AEnvelope
from backend.schemas import AgentMessage
from core.base_agent import BaseADKAgent
from tools.gemini_tool import GeminiToolError, normalize_language_with_gemini
from tools.profile_tool import load_user_profile


SPANISH_HINTS = {"dolor", "mareado", "pecho", "ayuda", "hospital"}


class LanguageAgent(BaseADKAgent):
    def __init__(self) -> None:
        super().__init__(
            key="language_agent",
            instruction=(
                "Translate the user's symptoms into clear, simple English, preserve meaning, "
                "and produce a concise normalized version for downstream clinical triage."
            ),
            tools={
                "profile_tool": load_user_profile,
                "language_llm_tool": normalize_language_with_gemini,
            },
        )

    def process(self, message: AgentMessage, envelope: A2AEnvelope) -> AgentMessage:
        profile = self.call_tool("profile_tool", message)
        lowered = message.raw_text.lower()
        fallback_language = "es" if any(token in lowered for token in SPANISH_HINTS) else profile["preferred_language"]
        normalized = " ".join(message.raw_text.strip().split())

        try:
            llm_result = self._run_language_reasoning(message)
            detected_language = str(llm_result["detected_language"]).lower()
            simplified_text = str(llm_result["simplified_text"]).strip()
            translated = str(llm_result["translated_text"]).strip()
        except (GeminiToolError, KeyError, TypeError, ValueError, RuntimeError):
            detected_language = fallback_language
            simplified_text = normalized
            translated = normalized

        message.detected_language = detected_language
        message.normalized_text = simplified_text
        message.translated_text = translated
        return message

    def _run_language_reasoning(self, message: AgentMessage) -> dict:
        if self.use_adk_runtime(message):
            return self.invoke_adk_json(
                message=message,
                prompt=(
                    "Normalize the following healthcare symptom report for downstream triage.\n\n"
                    f"User text: {message.raw_text}\n"
                    f"Preferred language: {message.preferred_language or 'unknown'}\n"
                    "Return structured JSON only."
                ),
                response_schema={
                    "type": "object",
                    "properties": {
                        "detected_language": {"type": "string"},
                        "simplified_text": {"type": "string"},
                        "translated_text": {"type": "string"},
                    },
                    "required": ["detected_language", "simplified_text", "translated_text"],
                },
            )
        return self.call_tool("language_llm_tool", message)
