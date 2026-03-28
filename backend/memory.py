from threading import Lock


class InMemorySessionStore:
    def __init__(self) -> None:
        self._data: dict[str, list[dict[str, str]]] = {}
        self._lock = Lock()

    def add_message(self, session_id: str, role: str, content: str) -> None:
        with self._lock:
            self._data.setdefault(session_id, []).append({"role": role, "content": content})

    def get_history(self, session_id: str) -> list[dict[str, str]]:
        with self._lock:
            return list(self._data.get(session_id, []))

    def clear_session(self, session_id: str) -> None:
        with self._lock:
            self._data.pop(session_id, None)


session_store = InMemorySessionStore()


def add_message(session_id: str, role: str, content: str) -> None:
    session_store.add_message(session_id, role, content)


def get_history(session_id: str) -> list[dict[str, str]]:
    return session_store.get_history(session_id)


def clear_session(session_id: str) -> None:
    session_store.clear_session(session_id)


def get_emergency_context(session_id: str, limit: int = 5) -> str:
    history = session_store.get_history(session_id)
    recent = history[-max(limit, 1) :]
    if not recent:
        return "No recent conversation history."

    return " | ".join(f"{msg.get('role', 'unknown')}: {msg.get('content', '')}" for msg in recent)


def get_history_context(session_id: str, limit: int = 8) -> str:
    history = session_store.get_history(session_id)
    recent = history[-max(limit, 1) :]
    if not recent:
        return ""

    return "\n".join(f"{msg.get('role', 'unknown')}: {msg.get('content', '')}" for msg in recent)