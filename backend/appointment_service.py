from __future__ import annotations

import json
from pathlib import Path
from threading import Lock
from uuid import uuid4

from pydantic import BaseModel, Field

from backend.firebase import FirebaseConfigError, get_firestore_client


_APPOINTMENTS_FILE = Path(__file__).resolve().parents[1] / ".data" / "appointments.json"
_APPOINTMENTS_LOCK = Lock()


class AppointmentRecord(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    user_id: str | None = None
    patient_name: str = "User"
    hospital: str | None = None
    date: str | None = None
    time: str | None = None
    doctor: str | None = None
    location: str | None = None
    instructions: str | None = None
    reason_for_visit: str = ""
    call_id: str = ""
    recording_url: str | None = None
    status: str = "confirmed"
    created_at: str


def _appointments_collection():
    db = get_firestore_client()
    return db.collection("appointments")


def _load_file_appointments() -> list[dict[str, object]]:
    if not _APPOINTMENTS_FILE.exists():
        return []

    try:
        data = json.loads(_APPOINTMENTS_FILE.read_text())
    except json.JSONDecodeError:
        return []

    return data if isinstance(data, list) else []


def _save_file_appointments(appointments: list[dict[str, object]]) -> None:
    _APPOINTMENTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    _APPOINTMENTS_FILE.write_text(json.dumps(appointments, indent=2, sort_keys=True))


def save_appointment(record: AppointmentRecord) -> AppointmentRecord:
    serialized = record.model_dump(mode="json")

    try:
        _appointments_collection().document(record.id).set(serialized)
    except FirebaseConfigError:
        with _APPOINTMENTS_LOCK:
            appointments = _load_file_appointments()
            appointments = [item for item in appointments if item.get("id") != record.id]
            appointments.append(serialized)
            _save_file_appointments(appointments)

    return record


def list_appointments(user_id: str) -> list[AppointmentRecord]:
    try:
        snapshots = _appointments_collection().where("user_id", "==", user_id).stream()
        records = [AppointmentRecord(**(snapshot.to_dict() or {})) for snapshot in snapshots]
    except FirebaseConfigError:
        with _APPOINTMENTS_LOCK:
            records = [
                AppointmentRecord(**item)
                for item in _load_file_appointments()
                if item.get("user_id") == user_id
            ]

    return sorted(records, key=lambda item: item.created_at, reverse=True)


def delete_appointment(user_id: str, appointment_id: str) -> bool:
    try:
        document = _appointments_collection().document(appointment_id)
        snapshot = document.get()
        if not snapshot.exists:
            return False
        payload = snapshot.to_dict() or {}
        if payload.get("user_id") != user_id:
            return False
        document.delete()
        return True
    except FirebaseConfigError:
        with _APPOINTMENTS_LOCK:
            appointments = _load_file_appointments()
            remaining = [
                item
                for item in appointments
                if not (item.get("id") == appointment_id and item.get("user_id") == user_id)
            ]
            deleted = len(remaining) != len(appointments)
            if deleted:
                _save_file_appointments(remaining)
            return deleted
