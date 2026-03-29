from __future__ import annotations

from threading import Lock

from backend.schemas import ChatSessionState


class InMemorySessionStore:
    def __init__(self) -> None:
        self._lock = Lock()
        self._sessions: dict[str, ChatSessionState] = {}

    def get(self, session_id: str) -> ChatSessionState | None:
        with self._lock:
            session = self._sessions.get(session_id)
            return session.model_copy(deep=True) if session else None

    def set(self, session_id: str, session: ChatSessionState) -> None:
        with self._lock:
            self._sessions[session_id] = session.model_copy(deep=True)


session_store = InMemorySessionStore()
