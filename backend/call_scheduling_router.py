from __future__ import annotations

from datetime import datetime, UTC, date, time

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field

from agents.message_types import A2AEnvelope
from backend.appointment_service import AppointmentRecord, delete_appointment, list_appointments, save_appointment
from backend.schemas import AgentMessage, HospitalLocation
from specialized.call_scheduling_agent import CallSchedulingAgent
from tools.gemini_tool import GeminiToolError, summarize_appointment_reason


router = APIRouter(prefix="/appointments", tags=["appointments"])


def _format_slot_date(value: str) -> str:
    raw = value.strip()
    if not raw:
        return raw

    try:
        parsed = date.fromisoformat(raw)
    except ValueError:
        return raw

    return parsed.strftime("%B %d").replace(" 0", " ")


def _format_slot_time(value: str) -> str:
    raw = value.strip()
    if not raw:
        return raw

    for fmt in ("%H:%M", "%H:%M:%S"):
        try:
            parsed = datetime.strptime(raw, fmt).time()
            return parsed.strftime("%I:%M %p").lstrip("0")
        except ValueError:
            continue

    return raw


def _format_slot(slot: AppointmentTimeSlotPayload) -> dict[str, str]:
    return {
        "date": _format_slot_date(slot.date),
        "time": _format_slot_time(slot.time),
    }


class AppointmentHospitalPayload(BaseModel):
    name: str
    address: str
    lat: float
    lng: float
    phone: str
    open_now: bool = True
    google_maps_uri: str | None = None


class AppointmentTimeSlotPayload(BaseModel):
    date: str
    time: str


class AppointmentRequest(BaseModel):
    patient_name: str = "User"
    reason_for_visit: str = "Medical consultation"
    location: str = ""
    time_slots: list[AppointmentTimeSlotPayload] = Field(default_factory=list)
    hospital: AppointmentHospitalPayload


class AppointmentSummaryRequest(BaseModel):
    chat_history: str = ""


class AppointmentSummaryResponse(BaseModel):
    summary: str


class AppointmentDetails(BaseModel):
    patient_name: str | None = None
    hospital: str | None = None
    date: str | None = None
    time: str | None = None
    doctor: str | None = None
    location: str | None = None
    instructions: str | None = None
    slot_index: int | None = None
    confirmed: bool = False


class AppointmentResponse(BaseModel):
    status: str
    call_id: str = ""
    appointment: AppointmentDetails | None = None
    slots_tried: list[dict[str, str]] = Field(default_factory=list)
    transcript: str = ""
    recording_url: str = ""
    error: str | None = None


class AppointmentListItem(BaseModel):
    id: str
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


class AppointmentListResponse(BaseModel):
    appointments: list[AppointmentListItem] = Field(default_factory=list)


@router.post("/summarize-reason", response_model=AppointmentSummaryResponse)
def summarize_reason(request: AppointmentSummaryRequest) -> AppointmentSummaryResponse:
    fallback_reason = "Medical consultation"

    try:
        summary = summarize_appointment_reason(request.chat_history.strip()) if request.chat_history.strip() else fallback_reason
    except GeminiToolError as exc:
        raise HTTPException(status_code=502, detail=f"Could not summarize conversation for scheduling: {exc}") from exc

    return AppointmentSummaryResponse(summary=summary)


@router.post("/call-hospital", response_model=AppointmentResponse)
def call_hospital(
    request: AppointmentRequest,
    x_user_id: str | None = Header(default=None, alias="x-user-id"),
) -> AppointmentResponse:
    user_id = (x_user_id or "").strip() or None
    summarized_reason = request.reason_for_visit.strip() or "Medical consultation"
    normalized_slots = [
        _format_slot(slot)
        for slot in request.time_slots
        if slot.date.strip() and slot.time.strip()
    ]
    if not normalized_slots:
        raise HTTPException(status_code=422, detail="At least one preferred time slot is required.")

    message = AgentMessage(
        user_id=user_id,
        location=request.location or request.hospital.address,
        raw_text=summarized_reason,
        hospitals=[HospitalLocation(**request.hospital.model_dump())],
        metadata={
            "patient_name": request.patient_name.strip() or "User",
            "reason_for_visit": summarized_reason,
            "hospital_name": request.hospital.name,
            "time_slots": normalized_slots,
            "max_wait_seconds": 180,
            "poll_interval": 5,
        },
    )
    envelope = A2AEnvelope(
        from_agent="root_agent",
        to_agent="call_scheduling_agent",
        intent="schedule_appointment",
        request_id=message.request_id,
        payload=message.model_dump(mode="json"),
        metadata={"protocol": "A2A", "local": True},
    )

    try:
        agent = CallSchedulingAgent()
        result_message = agent.process(message, envelope)
        result = result_message.metadata["appointment_result"]
        if result.get("status") == "confirmed" and result.get("appointment"):
            appointment = result["appointment"]
            save_appointment(
                AppointmentRecord(
                    user_id=message.user_id,
                    patient_name=message.metadata.get("patient_name", "User"),
                    hospital=appointment.get("hospital") or request.hospital.name,
                    date=appointment.get("date"),
                    time=appointment.get("time"),
                    doctor=appointment.get("doctor"),
                    location=appointment.get("location") or request.hospital.address,
                    instructions=appointment.get("instructions"),
                    reason_for_visit=message.metadata.get("reason_for_visit", summarized_reason),
                    call_id=result.get("call_id", ""),
                    recording_url=result.get("recording_url"),
                    status="confirmed",
                    created_at=datetime.now(UTC).isoformat(),
                )
            )
        return AppointmentResponse(**result)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Call scheduling failed: {exc}") from exc


@router.get("", response_model=AppointmentListResponse)
def get_appointments(
    x_user_id: str | None = Header(default=None, alias="x-user-id"),
) -> AppointmentListResponse:
    user_id = (x_user_id or "").strip()
    if not user_id:
        return AppointmentListResponse()

    appointments = list_appointments(user_id)
    return AppointmentListResponse(appointments=[AppointmentListItem(**item.model_dump(mode="json")) for item in appointments])


@router.delete("/{appointment_id}")
def delete_appointment_route(
    appointment_id: str,
    x_user_id: str | None = Header(default=None, alias="x-user-id"),
) -> dict[str, bool]:
    user_id = (x_user_id or "").strip()
    if not user_id:
        raise HTTPException(status_code=400, detail="Missing x-user-id header")

    deleted = delete_appointment(user_id, appointment_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Appointment not found")
    return {"deleted": True}
