from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from threading import Lock
from uuid import uuid4

from backend.firebase import FirebaseConfigError, get_firestore_client
from backend.visit_assistant.schemas import VisitSavedNote, VisitSaveNoteRequest


_NOTES_FILE = Path(__file__).resolve().parents[2] / ".data" / "visit_notes.json"
_NOTES_LOCK = Lock()


def _timestamp() -> str:
    return datetime.now(UTC).isoformat()


def _collection(user_id: str):
    db = get_firestore_client()
    return db.collection("users").document(user_id).collection("visit_notes")


def _load_file_notes() -> dict[str, list[dict[str, object]]]:
    if not _NOTES_FILE.exists():
        return {}

    try:
        return json.loads(_NOTES_FILE.read_text())
    except json.JSONDecodeError:
        return {}


def _save_file_notes(notes_by_user: dict[str, list[dict[str, object]]]) -> None:
    _NOTES_FILE.parent.mkdir(parents=True, exist_ok=True)
    _NOTES_FILE.write_text(json.dumps(notes_by_user, indent=2, sort_keys=True))


def list_visit_notes(user_id: str) -> list[VisitSavedNote]:
    try:
        documents = _collection(user_id).stream()
        notes = [VisitSavedNote(**document.to_dict()) for document in documents]
        return sorted(notes, key=lambda note: note.updated_at, reverse=True)
    except FirebaseConfigError:
        with _NOTES_LOCK:
            payload = _load_file_notes().get(user_id, [])
        notes = [VisitSavedNote(**item) for item in payload]
        return sorted(notes, key=lambda note: note.updated_at, reverse=True)


def save_visit_note(user_id: str, request: VisitSaveNoteRequest) -> VisitSavedNote:
    now = _timestamp()
    note = VisitSavedNote(
        id=str(uuid4()),
        title=request.title.strip(),
        transcript=request.transcript.strip(),
        summary=request.summary.strip(),
        structured_note=request.structured_note,
        created_at=now,
        updated_at=now,
    )
    serialized = note.model_dump(mode="json")

    try:
        _collection(user_id).document(note.id).set(serialized)
    except FirebaseConfigError:
        with _NOTES_LOCK:
            notes_by_user = _load_file_notes()
            user_notes = notes_by_user.setdefault(user_id, [])
            user_notes.append(serialized)
            _save_file_notes(notes_by_user)

    return note
