from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Callable

from agents.config import GEMINI_MODEL

try:
    from google.adk.agents.llm_agent import Agent as ADKAgent
    from google.adk.models.google_llm import Gemini
except ModuleNotFoundError:  # pragma: no cover - depends on local install
    ADKAgent = None
    Gemini = None


logger = logging.getLogger(__name__)
AgentHandler = Callable[[Any, dict[str, Any]], Any]


@dataclass
class BaseHealthcareAgent:
    key: str
    name: str
    instruction: str
    handler: AgentHandler
    adk_agent: Any = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def run(self, message: Any, context: dict[str, Any] | None = None) -> Any:
        safe_context = context or {}
        logger.info("agent=%s action=run payload=%s", self.name, message)
        return self.handler(message, safe_context)


def create_agent(
    *,
    key: str,
    name: str,
    instruction: str,
    handler: AgentHandler,
    metadata: dict[str, Any] | None = None,
) -> BaseHealthcareAgent:
    adk_agent = None
    if ADKAgent is not None and Gemini is not None:
        adk_agent = ADKAgent(
            name=name,
            model=Gemini(model=GEMINI_MODEL),
            instruction=instruction,
        )

    return BaseHealthcareAgent(
        key=key,
        name=name,
        instruction=instruction,
        handler=handler,
        adk_agent=adk_agent,
        metadata=metadata or {},
    )
