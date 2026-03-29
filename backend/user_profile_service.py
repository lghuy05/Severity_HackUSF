from __future__ import annotations

import json
from pathlib import Path
from threading import Lock

from backend.firebase import FirebaseConfigError, get_firestore_client
from backend.schemas import UserProfile


DEFAULT_PROFILE = UserProfile()
_PROFILE_FILE = Path(__file__).resolve().parents[1] / ".data" / "user_profiles.json"
_PROFILE_LOCK = Lock()


def _profile_document(user_id: str):
    db = get_firestore_client()
    return db.collection("users").document(user_id).collection("profile").document("default")


def _load_file_profiles() -> dict[str, dict[str, object]]:
    if not _PROFILE_FILE.exists():
        return {}

    try:
        return json.loads(_PROFILE_FILE.read_text())
    except json.JSONDecodeError:
        return {}


def _save_file_profiles(profiles: dict[str, dict[str, object]]) -> None:
    _PROFILE_FILE.parent.mkdir(parents=True, exist_ok=True)
    _PROFILE_FILE.write_text(json.dumps(profiles, indent=2, sort_keys=True))


def _normalize_profile(payload: dict[str, object] | None) -> UserProfile:
    return UserProfile(**(payload or {}))


def _read_profile(user_id: str) -> UserProfile | None:
    try:
        snapshot = _profile_document(user_id).get()
    except FirebaseConfigError:
        with _PROFILE_LOCK:
            stored = _load_file_profiles().get(user_id)
        return _normalize_profile(stored) if stored else None

    if not snapshot.exists:
        return None

    return _normalize_profile(snapshot.to_dict())


def _write_profile(user_id: str, profile: UserProfile) -> UserProfile:
    serialized = profile.model_dump(mode="json")

    try:
        _profile_document(user_id).set(serialized, merge=True)
    except FirebaseConfigError:
        with _PROFILE_LOCK:
            profiles = _load_file_profiles()
            profiles[user_id] = serialized
            _save_file_profiles(profiles)

    return profile


def get_or_create_profile(user_id: str) -> UserProfile:
    profile = _read_profile(user_id)
    if profile is not None:
        return profile
    return _write_profile(user_id, DEFAULT_PROFILE.model_copy(deep=True))


def update_profile(user_id: str, patch: dict[str, object]) -> UserProfile:
    current = get_or_create_profile(user_id)
    merged = current.model_copy(update=patch)
    return _write_profile(user_id, merged)
