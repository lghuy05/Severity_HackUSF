from __future__ import annotations

import logging
import os
from abc import ABC, abstractmethod
from typing import Any, Callable

from agents.config import get_gemini_model
from agents.message_types import A2AEnvelope
from backend.schemas import AgentMessage
from core.adk_runtime import ADKRuntimeError, parse_adk_json_output, run_adk_structured_agent
from core.tracing import append_trace, trace_span


logger = logging.getLogger(__name__)
ToolFn = Callable[[AgentMessage], Any]


class BaseADKAgent(ABC):
    def __init__(
        self,
        *,
        key: str,
        instruction: str,
        tools: dict[str, ToolFn] | None = None,
    ) -> None:
        self.key = key
        self.instruction = instruction
        self.tools = tools or {}
        self.adk_agent = self._build_adk_agent()

    def _build_adk_agent(self) -> Any | None:
        try:
            from google.adk.agents.llm_agent import Agent as ADKAgent
        except ModuleNotFoundError:
            return None

        model = get_gemini_model()
        if model is None:
            return None

        return ADKAgent(
            name=self.key,
            model=model,
            instruction=self.instruction,
            tools=list(self.tools.values()),
        )

    def call_tool(self, tool_name: str, message: AgentMessage) -> Any:
        append_trace(
            message,
            event="tool_called",
            agent=self.key,
            tool=tool_name,
            detail=f"{self.key} invoked {tool_name}",
        )
        return self.tools[tool_name](message)

    def use_adk_runtime(self, message: AgentMessage | None = None) -> bool:
        if message is not None and "use_adk" in message.metadata:
            return bool(message.metadata["use_adk"])
        return os.getenv("USE_ADK_RUNTIME", "0") == "1"

    def invoke_adk_json(
        self,
        *,
        message: AgentMessage,
        prompt: str,
        response_schema: dict[str, Any],
    ) -> dict[str, Any]:
        append_trace(
            message,
            event="tool_called",
            agent=self.key,
            tool="adk_runtime",
            detail=f"{self.key} invoked ADK runtime",
        )
        result = run_adk_structured_agent(
            agent_name=self.key,
            instruction=self.instruction,
            prompt=prompt,
            response_schema=response_schema,
        )
        append_trace(
            message,
            event="tool_called",
            agent=self.key,
            tool="adk_runtime_result",
            detail=f"{self.key} received {len(result.raw_events)} ADK events",
        )
        return parse_adk_json_output(result)

    def run(self, message: AgentMessage, envelope: A2AEnvelope) -> AgentMessage:
        with trace_span(
            message,
            start_event="agent_started",
            finish_event="agent_completed",
            agent=self.key,
            intent=envelope.intent,
            detail=f"{envelope.from_agent} -> {envelope.to_agent}",
        ):
            logger.info(
                "agent_run",
                extra={
                    "event_data": {
                        "event": "agent_started",
                        "request_id": message.request_id,
                        "agent": self.key,
                        "intent": envelope.intent,
                    }
                },
            )
            return self.process(message, envelope)

    @abstractmethod
    def process(self, message: AgentMessage, envelope: A2AEnvelope) -> AgentMessage:
        raise NotImplementedError
