from __future__ import annotations

from backend.schemas import AgentMessage


def export_a2a_trace(message: AgentMessage) -> list[dict]:
    return [event.model_dump(mode="json") for event in message.trace]
