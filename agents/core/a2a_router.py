from __future__ import annotations

import logging
from dataclasses import asdict, dataclass, field
from typing import Any

from agents.core.agent_registry import get_agent


logger = logging.getLogger(__name__)


@dataclass
class A2AMessage:
    from_agent: str
    to_agent: str
    payload: Any
    intent: str
    metadata: dict[str, Any] = field(default_factory=dict)


def route(
    message: Any,
    from_agent: str,
    to_agent: str,
    *,
    intent: str,
    context: dict[str, Any] | None = None,
    trace: list[dict[str, Any]] | None = None,
) -> Any:
    envelope = A2AMessage(
        from_agent=from_agent,
        to_agent=to_agent,
        payload=message,
        intent=intent,
        metadata={"a2a": True},
    )
    logger.info("a2a_route=%s", envelope)
    response = get_agent(to_agent).run(message, context=context)

    if trace is not None:
        trace.append(
            {
                "message": asdict(envelope),
                "response_type": type(response).__name__,
            }
        )

    return response
