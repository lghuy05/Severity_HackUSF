from __future__ import annotations

from agents.message_types import A2AEnvelope
from backend.schemas import AgentMessage
from core.base_agent import BaseADKAgent
from core.tracing import append_trace
from tools.gemini_tool import GeminiToolError, assess_triage_with_gemini


HIGH_RISK_KEYWORDS = {
    "chest pain",
    "shortness of breath",
    "trouble breathing",
    "stroke",
    "fainted",
    "severe bleeding",
    "dizzy",
    "dizziness",
    "unconscious",
}
MEDIUM_RISK_KEYWORDS = {"fever", "infection", "vomiting", "asthma", "dehydrated", "migraine"}
HIGH_RISK_GROUPS = [
    {"chest pain", "dizzy"},
    {"chest pain", "dizziness"},
]
HIGH_RISK_SINGLE = {
    "shortness of breath",
    "trouble breathing",
    "difficulty breathing",
    "breathing difficulty",
    "stroke",
    "fainted",
    "severe bleeding",
    "unconscious",
}


class TriageAgent(BaseADKAgent):
    def __init__(self) -> None:
        super().__init__(
            key="triage_agent",
            instruction=(
                "Extract symptoms and explain severity hints from a healthcare symptom report. "
                "Do not make the final triage decision for the system. "
                "Return structured JSON with symptoms, a suggested severity hint, reasoning, and a recommended action."
            ),
            tools={"triage_llm_tool": assess_triage_with_gemini},
        )

    def process(self, message: AgentMessage, envelope: A2AEnvelope) -> AgentMessage:
        normalized = (message.translated_text or message.normalized_text or message.raw_text).lower()
        triage_context = self._run_triage_reasoning(message)
        risk_level, risk_reason = self._deterministic_risk_decision(message, normalized, triage_context)

        message.risk_level = risk_level
        message.risk_reason = risk_reason
        return message

    def _run_triage_reasoning(self, message: AgentMessage) -> dict:
        normalized_text = message.translated_text or message.normalized_text or message.raw_text
        if self.use_adk_runtime(message):
            return self.invoke_adk_json(
                message=message,
                prompt=(
                    "Extract symptoms and explain severity hints from the following healthcare report. "
                    "The system will make the final triage decision in code. "
                    "Return JSON only.\n\n"
                    f"User text: {normalized_text}\n"
                    f"Location: {message.location}"
                ),
                response_schema={
                    "type": "object",
                    "properties": {
                        "risk_level": {
                            "type": "string",
                            "enum": ["low", "medium", "high"],
                        },
                        "reasoning": {"type": "string"},
                        "symptoms": {
                            "type": "array",
                            "items": {"type": "string"},
                        },
                        "recommended_action": {"type": "string"},
                    },
                    "required": ["risk_level", "reasoning", "symptoms", "recommended_action"],
                },
            )

        try:
            llm_result = self.call_tool("triage_llm_tool", message)
            return {
                "risk_level": str(llm_result["risk_level"]).lower(),
                "reasoning": str(llm_result["risk_reason"]).strip(),
                "symptoms": self._extract_symptoms_from_text(normalized_text),
                "recommended_action": "Seek prompt care based on symptom severity.",
            }
        except (GeminiToolError, KeyError, TypeError, ValueError):
            append_trace(
                message,
                event="tool_called",
                agent=self.key,
                tool="triage_fallback",
                detail="triage_agent used deterministic fallback context",
            )
            return {
                "risk_level": "low",
                "reasoning": "Fallback triage context generated from deterministic rules.",
                "symptoms": self._extract_symptoms_from_text(normalized_text),
                "recommended_action": "Monitor symptoms and seek care if they worsen.",
            }

    def _deterministic_risk_decision(self, message: AgentMessage, normalized: str, triage_context: dict) -> tuple[str, str]:
        extracted_symptoms = {
            symptom.strip().lower()
            for symptom in triage_context.get("symptoms", [])
            if isinstance(symptom, str) and symptom.strip()
        }
        extracted_symptoms.update(self._extract_symptoms_from_text(normalized))

        if any(group.issubset(extracted_symptoms) for group in HIGH_RISK_GROUPS):
            append_trace(
                message,
                event="tool_called",
                agent=self.key,
                tool="triage_decision_override",
                detail="Deterministic rules set final risk to high for chest pain plus dizziness",
            )
            return (
                "high",
                self._merge_reasoning(
                    "Chest pain with dizziness is treated as high risk and needs immediate evaluation.",
                    triage_context,
                ),
            )

        if extracted_symptoms.intersection(HIGH_RISK_SINGLE):
            append_trace(
                message,
                event="tool_called",
                agent=self.key,
                tool="triage_decision_override",
                detail="Deterministic rules set final risk to high for severe respiratory or emergency symptoms",
            )
            return (
                "high",
                self._merge_reasoning(
                    "Breathing difficulty or other emergency symptoms are treated as high risk and require urgent evaluation.",
                    triage_context,
                ),
            )

        if any(keyword in normalized for keyword in MEDIUM_RISK_KEYWORDS):
            append_trace(
                message,
                event="tool_called",
                agent=self.key,
                tool="triage_decision_override",
                detail="Deterministic rules set final risk to medium",
            )
            return (
                "medium",
                self._merge_reasoning(
                    "Symptoms suggest prompt medical follow-up, but they do not appear immediately life-threatening.",
                    triage_context,
                ),
            )

        append_trace(
            message,
            event="tool_called",
            agent=self.key,
            tool="triage_decision_override",
            detail="Deterministic rules set final risk to low",
        )
        return (
            "low",
            self._merge_reasoning(
                "Symptoms appear lower risk based on deterministic thresholds and current information.",
                triage_context,
            ),
        )

    def _extract_symptoms_from_text(self, text: str) -> set[str]:
        detected: set[str] = set()
        for keyword in HIGH_RISK_KEYWORDS.union(HIGH_RISK_SINGLE).union(MEDIUM_RISK_KEYWORDS):
            if keyword in text.lower():
                detected.add(keyword)
        if "difficulty breathing" in text.lower():
            detected.add("difficulty breathing")
        return detected

    def _merge_reasoning(self, deterministic_reason: str, triage_context: dict) -> str:
        llm_reasoning = str(triage_context.get("reasoning", "")).strip()
        action = str(triage_context.get("recommended_action", "")).strip()
        parts = [deterministic_reason]
        if llm_reasoning:
            parts.append(f"LLM context: {llm_reasoning}")
        if action:
            parts.append(f"Suggested action: {action}")
        return " ".join(parts)
