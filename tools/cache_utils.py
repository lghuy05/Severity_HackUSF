from __future__ import annotations

import time
from typing import Callable, TypeVar


T = TypeVar("T")


class TTLCache:
    def __init__(self, ttl_seconds: int = 300) -> None:
        self.ttl_seconds = ttl_seconds
        self._store: dict[str, tuple[float, object]] = {}

    def get_or_set(self, key: str, factory: Callable[[], T]) -> T:
        now = time.time()
        cached = self._store.get(key)
        if cached and now - cached[0] < self.ttl_seconds:
          return cached[1]  # type: ignore[return-value]

        value = factory()
        self._store[key] = (now, value)
        return value
