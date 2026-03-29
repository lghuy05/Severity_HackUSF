from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class A2AEnvelope:
    from_agent: str
    to_agent: str
    intent: str
    request_id: str
    payload: dict[str, Any]
    metadata: dict[str, Any] = field(default_factory=dict)
