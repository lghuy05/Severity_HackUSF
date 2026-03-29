from __future__ import annotations

from backend.schemas import AgentMessage


def load_user_profile(message: AgentMessage) -> dict[str, str]:
    preferred_language = message.preferred_language or "en"
    return {
        "user_id": message.user_id or "anonymous",
        "preferred_language": preferred_language,
        "contact_preference": "phone",
    }
