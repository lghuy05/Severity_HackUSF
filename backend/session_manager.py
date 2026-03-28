"""
Thread-safe, in-memory session / conversation-history manager.

Maps  session_id (str) → list[dict]   where each dict looks like:
    {"role": "user"|"assistant"|"system", "content": "..."}
"""

import threading
from typing import Dict, List


_store: Dict[str, List[dict]] = {}
_lock = threading.Lock()


def add_message(session_id: str, role: str, content: str) -> None:
    """Append a message to the session's conversation history."""
    with _lock:
        _store.setdefault(session_id, []).append(
            {"role": role, "content": content}
        )


def get_history(session_id: str) -> List[dict]:
    """Return a *copy* of the conversation history for a session."""
    with _lock:
        return list(_store.get(session_id, []))


def clear_session(session_id: str) -> None:
    """Delete all history for a session."""
    with _lock:
        _store.pop(session_id, None)


def list_sessions() -> List[str]:
    """Return all active session IDs."""
    with _lock:
        return list(_store.keys())


def get_emergency_context(session_id: str, limit: int = 5) -> str:
    """
    Extract the last *limit* messages and format them into a concise string.

    Designed for the Emergency Agent – provides fast, relevant context
    without bloating the dispatch payload with older chat history.

    Returns something like:
        [user] I have severe chest pain and can't breathe
        [assistant] I'm escalating this immediately...
    """
    with _lock:
        messages = _store.get(session_id, [])[-limit:]
    if not messages:
        return "(no prior conversation)"
    return "\n".join(
        f"[{m['role']}] {m['content']}" for m in messages
    )
