from __future__ import annotations

from agents.message_types import A2AEnvelope
from agents.registry import AgentRegistry
from backend.schemas import AgentMessage
from core.tracing import append_trace


class A2ARouter:
    def __init__(self, registry: AgentRegistry) -> None:
        self.registry = registry

    def handoff(self, message: AgentMessage, *, from_agent: str, to_agent: str, intent: str) -> AgentMessage:
        envelope = A2AEnvelope(
            from_agent=from_agent,
            to_agent=to_agent,
            intent=intent,
            request_id=message.request_id,
            payload=message.model_dump(mode="json"),
            metadata={"protocol": "A2A", "local": True},
        )
        append_trace(
            message,
            event="handoff_to_agent",
            agent=from_agent,
            next_agent=to_agent,
            intent=intent,
            detail="Structured A2A delegation",
        )
        agent = self.registry.get(to_agent)
        return agent.run(message, envelope)
