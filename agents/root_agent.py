from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from agents.communication_agent import communication_agent
from agents.config import GEMINI_MODEL
from agents.core.a2a_router import route
from agents.emergency_agent import emergency_agent
from agents.language_agent import language_agent
from agents.navigation_agent import navigation_agent
from agents.summary_agent import summary_agent
from agents.triage_agent import triage_agent
from shared.schemas import AnalyzeResponse, CommunicationResponse, EmergencyOutput

try:
    from google.adk.agents.llm_agent import Agent as ADKAgent
    from google.adk.models.google_llm import Gemini
except ModuleNotFoundError:  # pragma: no cover - depends on local install
    ADKAgent = None
    Gemini = None


logger = logging.getLogger(__name__)


@dataclass
class RootHealthcareAgent:
    name: str = "healthcare_root_agent"
    sub_agents: list[Any] = field(
        default_factory=lambda: [
            language_agent,
            triage_agent,
            navigation_agent,
            summary_agent,
            communication_agent,
            emergency_agent,
        ]
    )
    adk_agent: Any = None

    def __post_init__(self):
        if ADKAgent is not None and Gemini is not None:
            self.adk_agent = ADKAgent(
                name=self.name,
                model=Gemini(model=GEMINI_MODEL),
                instruction=(
                    "You are a master healthcare agent. Delegate tasks in this order: "
                    "language to triage to navigation to summary. Trigger the emergency agent for high risk cases "
                    "and use the communication agent for provider handoff."
                ),
                sub_agents=[agent.adk_agent for agent in self.sub_agents if agent.adk_agent is not None],
            )

    def run(self, user_input: str, location: str = "Unknown location") -> AnalyzeResponse:
        trace: list[dict[str, Any]] = []
        context = {"location": location}

        language_output = route(
            user_input,
            "root",
            "language",
            intent="normalize_user_message",
            context=context,
            trace=trace,
        )
        triage = route(
            language_output.translated_text,
            "language",
            "triage",
            intent="assess_medical_risk",
            context=context,
            trace=trace,
        )

        emergency: EmergencyOutput
        if triage.risk_level == "high":
            emergency = route(
                triage.risk_level,
                "triage",
                "emergency",
                intent="issue_urgent_guidance",
                context=context,
                trace=trace,
            )
        else:
            emergency = emergency_agent.run(triage.risk_level, context=context)

        navigation = route(
            {"risk_level": triage.risk_level, "location": location},
            "triage",
            "navigation",
            intent="find_care_destinations",
            context=context,
            trace=trace,
        )
        summary = route(
            {
                "original_text": user_input,
                "location": location,
                "language_output": language_output,
                "triage": triage,
                "navigation": navigation,
                "emergency": emergency,
            },
            "navigation",
            "summary",
            intent="build_structured_summary",
            context=context,
            trace=trace,
        )
        provider_message: CommunicationResponse = route(
            summary,
            "summary",
            "communication",
            intent="create_provider_handoff",
            context=context,
            trace=trace,
        )

        logger.info("a2a_trace=%s", trace)

        return AnalyzeResponse(
            language_output=language_output,
            triage=triage,
            navigation=navigation,
            summary=summary,
            provider_message=provider_message.message,
            emergency_flag=emergency.emergency_flag,
            emergency=emergency,
        )


root_agent = RootHealthcareAgent()


def run_pipeline(user_input: str, location: str = "Unknown location") -> AnalyzeResponse:
    return root_agent.run(user_input=user_input, location=location)
