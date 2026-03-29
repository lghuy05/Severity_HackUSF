from __future__ import annotations

import logging
from time import perf_counter
from typing import Iterator

from backend.schemas import AgentMessage, TraceEvent


logger = logging.getLogger(__name__)


def append_trace(
    message: AgentMessage,
    *,
    event: str,
    agent: str | None = None,
    next_agent: str | None = None,
    intent: str | None = None,
    tool: str | None = None,
    latency_ms: int | None = None,
    detail: str | None = None,
    error: str | None = None,
) -> TraceEvent:
    trace_event = TraceEvent(
        event=event,
        request_id=message.request_id,
        agent=agent,
        next_agent=next_agent,
        intent=intent,
        tool=tool,
        latency_ms=latency_ms,
        detail=detail,
        error=error,
        state_fields=message.visible_fields(),
    )
    message.trace.append(trace_event)
    logger.info(
        event,
        extra={
            "event_data": {
                "event": event,
                "request_id": message.request_id,
                "agent": agent,
                "next_agent": next_agent,
                "intent": intent,
                "tool": tool,
                "latency_ms": latency_ms,
                "detail": detail,
                "error": error,
            }
        },
    )
    return trace_event


class trace_span:
    def __init__(
        self,
        message: AgentMessage,
        *,
        start_event: str,
        finish_event: str,
        agent: str | None = None,
        next_agent: str | None = None,
        intent: str | None = None,
        tool: str | None = None,
        detail: str | None = None,
    ) -> None:
        self.message = message
        self.start_event = start_event
        self.finish_event = finish_event
        self.agent = agent
        self.next_agent = next_agent
        self.intent = intent
        self.tool = tool
        self.detail = detail
        self.started = 0.0

    def __enter__(self) -> "trace_span":
        self.started = perf_counter()
        append_trace(
            self.message,
            event=self.start_event,
            agent=self.agent,
            next_agent=self.next_agent,
            intent=self.intent,
            tool=self.tool,
            detail=self.detail,
        )
        return self

    def __exit__(self, exc_type, exc, _tb) -> None:
        latency_ms = int((perf_counter() - self.started) * 1000)
        append_trace(
            self.message,
            event=self.finish_event if exc is None else "pipeline_failed",
            agent=self.agent,
            next_agent=self.next_agent,
            intent=self.intent,
            tool=self.tool,
            latency_ms=latency_ms,
            detail=self.detail,
            error=str(exc) if exc else None,
        )
