from __future__ import annotations

from typing import Iterable

from core.base_agent import BaseADKAgent


class AgentRegistry:
    def __init__(self, agents: Iterable[BaseADKAgent]) -> None:
        self._agents = {agent.key: agent for agent in agents}

    def get(self, key: str) -> BaseADKAgent:
        return self._agents[key]

    def keys(self) -> list[str]:
        return sorted(self._agents)
