from __future__ import annotations

import logging
import os
import re
import time
from typing import Any

import requests

from agents.message_types import A2AEnvelope
from backend.schemas import AgentMessage
from core.base_agent import BaseADKAgent
from tools.gemini_tool import GeminiToolError, generate_structured_json


logger = logging.getLogger(__name__)

VAPI_API_KEY = os.environ.get("VAPI_API_KEY", "")
VAPI_ASSISTANT_ID = os.environ.get("VAPI_ASSISTANT_ID", "")
VAPI_PHONE_NUMBER_ID = os.environ.get("VAPI_PHONE_NUMBER_ID", "")
VAPI_TO_NUMBER = os.environ.get("VAPI_TO_NUMBER", "")
VAPI_BASE_URL = "https://api.vapi.ai"

_ORDINAL_PATTERNS: list[tuple[int, tuple[str, ...]]] = [
    (0, ("first option", "option one", "option 1", "first slot", "slot one", "slot 1", "the first one", "1st option")),
    (1, ("second option", "option two", "option 2", "second slot", "slot two", "slot 2", "the second one", "2nd option")),
    (2, ("third option", "option three", "option 3", "third slot", "slot three", "slot 3", "the third one", "3rd option")),
]


def make_appointment_call(message: AgentMessage) -> dict[str, Any]:
    patient_name = str(message.metadata.get("patient_name", "Unknown Patient")).strip()
    reason_for_visit = str(message.metadata.get("reason_for_visit", "Medical consultation")).strip()
    hospital_name = (
        str(message.metadata.get("hospital_name", ""))
        or (message.hospitals[0].name if message.hospitals else "Healthcare Facility")
    ).strip()

    time_slots = message.metadata.get("time_slots")

    if not time_slots:
        preferred_date = str(message.metadata.get("preferred_date", "")).strip()
        preferred_time = str(message.metadata.get("preferred_time", "")).strip()
        if preferred_date or preferred_time:
            time_slots = [{"date": preferred_date, "time": preferred_time}]

    if not time_slots:
        logger.error("No time slots provided")
        return {"call_id": "", "status": "error", "message": "No time slots provided"}

    time_slots = time_slots[:3]
    logger.info("Scheduling with %s time slot(s): %s", len(time_slots), time_slots)

    slots_list: list[str] = []
    for i, slot in enumerate(time_slots, 1):
        slot_date = slot.get("date", "")
        slot_time = slot.get("time", "")
        slots_list.append(f"{i}. {slot_time} on {slot_date}")

    available_slots = "\n".join(slots_list)

    payload = {
        "assistantId": VAPI_ASSISTANT_ID,
        "phoneNumberId": VAPI_PHONE_NUMBER_ID,
        "customer": {
            "number": VAPI_TO_NUMBER,
        },
        "assistantOverrides": {
            "variableValues": {
                "patient": {
                    "fullName": patient_name,
                },
                "reason_for_visit": reason_for_visit,
                "hospital_name": hospital_name,
                "available_slots": available_slots,
                "num_slots": str(len(time_slots)),
            }
        },
    }

    headers = {
        "Authorization": VAPI_API_KEY,
        "Content-Type": "application/json",
    }

    logger.debug("Vapi request - API key present: %s, API key length: %s", bool(VAPI_API_KEY), len(VAPI_API_KEY))
    logger.debug("Vapi request - Assistant ID: %s, Phone Number ID: %s", VAPI_ASSISTANT_ID, VAPI_PHONE_NUMBER_ID)
    logger.debug("Available slots for call: %s", available_slots)

    try:
        response = requests.post(f"{VAPI_BASE_URL}/call/phone", json=payload, headers=headers, timeout=30)

        if response.status_code in (200, 201):
            data = response.json()
            call_id = data.get("id", "")
            logger.info("Vapi call initiated with %s time slot(s): call_id=%s", len(time_slots), call_id)
            return {"call_id": call_id, "status": "initiated", "message": "Call queued with Vapi", "num_slots": len(time_slots)}

        logger.error("Vapi error %s: %s", response.status_code, response.text)
        if response.status_code == 401:
            logger.error("Authentication failed. Verify your VAPI_API_KEY is correct.")
        return {"call_id": "", "status": "error", "message": f"Vapi {response.status_code}: {response.text}"}
    except Exception as exc:
        logger.error("Exception calling Vapi: %s", exc)
        return {"call_id": "", "status": "error", "message": f"Exception: {str(exc)}"}


def get_call_status(call_id: str) -> dict[str, Any]:
    if not call_id:
        return {"call_id": "", "status": "error", "ended_reason": "No call_id provided"}

    headers = {"Authorization": VAPI_API_KEY}

    try:
        response = requests.get(f"{VAPI_BASE_URL}/call/{call_id}", headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return {
                "call_id": call_id,
                "status": data.get("status", "unknown"),
                "ended_reason": data.get("endedReason", ""),
            }

        logger.error("get_call_status failed: %s - %s", response.status_code, response.text)
        return {"call_id": call_id, "status": "error", "ended_reason": response.text}
    except Exception as exc:
        logger.error("Exception in get_call_status: %s", exc)
        return {"call_id": call_id, "status": "error", "ended_reason": str(exc)}


def get_call_transcript(call_id: str) -> dict[str, Any]:
    if not call_id:
        return {
            "call_id": "",
            "transcript": "",
            "recording_url": "",
            "duration_seconds": 0,
        }

    headers = {"Authorization": VAPI_API_KEY}

    try:
        response = requests.get(f"{VAPI_BASE_URL}/call/{call_id}", headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            messages = data.get("messages", [])
            transcript_lines: list[str] = []
            for msg in messages:
                role = msg.get("role", "unknown")
                content = msg.get("message", "")
                if content:
                    transcript_lines.append(f"{role}: {content}")

            return {
                "call_id": call_id,
                "transcript": "\n".join(transcript_lines),
                "recording_url": data.get("recordingUrl", "") or "",
                "duration_seconds": 0,
            }

        logger.error("get_call_transcript failed: %s", response.status_code)
        return {
            "call_id": call_id,
            "transcript": "",
            "recording_url": "",
            "duration_seconds": 0,
        }
    except Exception as exc:
        logger.error("Exception in get_call_transcript: %s", exc)
        return {
            "call_id": call_id,
            "transcript": "",
            "recording_url": "",
            "duration_seconds": 0,
        }


def wait_for_call_completion(call_id: str, max_wait_seconds: int = 120, poll_interval: int = 5) -> dict[str, Any]:
    if not call_id:
        return {"call_id": "", "status": "error", "ended_reason": "No call_id provided"}

    start_time = time.time()
    while True:
        elapsed = time.time() - start_time
        if elapsed > max_wait_seconds:
            logger.warning("Call %s timeout after %.1fs", call_id, elapsed)
            return {"call_id": call_id, "status": "timeout", "ended_reason": "Max wait time exceeded"}

        status_result = get_call_status(call_id)
        current_status = status_result.get("status", "")

        if current_status == "ended":
            logger.info("Call %s completed with reason: %s", call_id, status_result.get("ended_reason"))
            return status_result

        if current_status == "error":
            return status_result

        logger.info("Call %s status: %s, elapsed: %.1fs", call_id, current_status, elapsed)
        time.sleep(poll_interval)


def schedule_appointment_with_vapi(message: AgentMessage) -> dict[str, Any]:
    patient_name = str(message.metadata.get("patient_name", "Unknown Patient")).strip()
    hospital_name = (
        str(message.metadata.get("hospital_name", ""))
        or (message.hospitals[0].name if message.hospitals else "Healthcare Facility")
    ).strip()

    time_slots = message.metadata.get("time_slots")
    if not time_slots:
        preferred_date = str(message.metadata.get("preferred_date", "")).strip()
        preferred_time = str(message.metadata.get("preferred_time", "")).strip()
        if preferred_date or preferred_time:
            time_slots = [{"date": preferred_date, "time": preferred_time}]

    if not time_slots:
        logger.error("No time slots provided")
        return {
            "status": "failed",
            "call_id": "",
            "appointment": None,
            "slots_tried": [],
            "transcript": "",
            "recording_url": "",
            "error": "No time slots provided",
        }

    max_wait_seconds = int(message.metadata.get("max_wait_seconds", 180))
    poll_interval = int(message.metadata.get("poll_interval", 5))

    logger.info("Starting appointment scheduling for %s", patient_name)
    logger.info("Available time slots: %s", time_slots)

    call_result = make_appointment_call(message)
    if call_result["status"] == "error":
        logger.error("STEP 1 failed: %s", call_result["message"])
        return {
            "status": "failed",
            "call_id": "",
            "appointment": None,
            "slots_tried": time_slots,
            "transcript": "",
            "recording_url": "",
            "error": call_result["message"],
        }

    call_id = call_result.get("call_id", "")
    wait_result = wait_for_call_completion(call_id, max_wait_seconds, poll_interval)
    if wait_result["status"] in ["error", "timeout"]:
        return {
            "status": "failed",
            "call_id": call_id,
            "appointment": None,
            "slots_tried": time_slots,
            "transcript": "",
            "recording_url": "",
            "error": f"Call did not complete: {wait_result['ended_reason']}",
        }

    transcript_result = get_call_transcript(call_id)
    transcript = transcript_result.get("transcript", "")
    recording_url = transcript_result.get("recording_url", "")
    logger.info("Retrieved call transcript for %s with %s characters", call_id, len(transcript))
    if transcript:
        logger.info("Call transcript preview for %s: %s", call_id, transcript[:1200])
    appointment_details = _extract_appointment_details(transcript, patient_name, hospital_name, time_slots)
    final_status = "confirmed" if appointment_details["confirmed"] and appointment_details["slot_index"] is not None else "failed"
    logger.info(
        "Appointment extraction result for %s: final_status=%s confirmed=%s slot_index=%s date=%s time=%s",
        call_id,
        final_status,
        appointment_details["confirmed"],
        appointment_details["slot_index"],
        appointment_details["date"],
        appointment_details["time"],
    )

    return {
        "status": final_status,
        "call_id": call_id,
        "appointment": appointment_details,
        "slots_tried": time_slots,
        "transcript": transcript,
        "recording_url": recording_url,
    }


def _extract_appointment_details(transcript: str, patient_name: str, hospital_name: str, time_slots: list[Any]) -> dict[str, Any]:
    """
    Uses Gemini to read and understand the full call transcript and extract
    which slot was confirmed, if any. Never fabricates details.
    """
    details = {
        "patient_name": patient_name,
        "hospital": hospital_name,
        "date": None,
        "time": None,
        "doctor": None,
        "location": None,
        "instructions": None,
        "slot_index": None,
        "confirmed": False,
    }

    if not transcript:
        logger.warning("Empty transcript received, returning unconfirmed details")
        return details

    slots_text = "\n".join([
        f"Slot {i}: {s.get('date', '')} at {s.get('time', '')}"
        for i, s in enumerate(time_slots)
    ])

    prompt = f"""
You are analyzing a phone call transcript between a medical scheduling assistant and a hospital receptionist.

The assistant offered these time slots during the call:
{slots_text}

Here is the full transcript of the call:
{transcript}

Based ONLY on what was actually said in the transcript, answer the following.
Do not guess, assume, or infer anything that was not explicitly stated.

Return your answer as a JSON object with exactly these fields:
{{
  "confirmed": true or false,
  "slot_index": 0, 1, 2, or null if no slot was confirmed,
  "date": the confirmed date as mentioned in the transcript or null,
  "time": the confirmed time as mentioned in the transcript or null,
  "doctor": doctor name if explicitly mentioned in the transcript or null,
  "location": department or location if explicitly mentioned in the transcript or null,
  "instructions": any special instructions explicitly mentioned in the transcript or null
}}

Rules you must follow:
- Set "confirmed" to true if the conversation clearly shows the appointment was successfully booked or scheduled, even if the exact phrase "the appointment is confirmed" was not used
- Accept natural confirmation language such as "you're all set", "we have you scheduled", "that works", "booked", "scheduled", or other clear final booking language
- Set "slot_index" to whichever slot number from the list above was confirmed (0, 1, or 2)
- If the receptionist rejected all slots, was unavailable, or the call ended without a clear confirmation, set confirmed to false and slot_index to null
- If you are not sure whether something was confirmed, set confirmed to false — do not guess
- Only return the raw JSON object, no markdown, no explanation, nothing else
"""

    try:
        logger.info("Sending transcript to Gemini for intelligent extraction")
        extracted = generate_structured_json(
            prompt=prompt,
            schema={
                "type": "object",
                "properties": {
                    "confirmed": {"type": "boolean"},
                    "slot_index": {"type": ["integer", "null"]},
                    "date": {"type": ["string", "null"]},
                    "time": {"type": ["string", "null"]},
                    "doctor": {"type": ["string", "null"]},
                    "location": {"type": ["string", "null"]},
                    "instructions": {"type": ["string", "null"]},
                },
                "required": [
                    "confirmed",
                    "slot_index",
                    "date",
                    "time",
                    "doctor",
                    "location",
                    "instructions",
                ],
            },
        )
        logger.info("Gemini parsed extraction payload: %s", extracted)

        details["confirmed"] = extracted.get("confirmed", False)
        details["slot_index"] = extracted.get("slot_index", None)
        details["date"] = extracted.get("date", None)
        details["time"] = extracted.get("time", None)
        details["doctor"] = extracted.get("doctor", None)
        details["location"] = extracted.get("location", None)
        details["instructions"] = extracted.get("instructions", None)

        logger.info(
            "Gemini extraction complete: confirmed=%s, slot_index=%s, date=%s, time=%s",
            details["confirmed"],
            details["slot_index"],
            details["date"],
            details["time"],
        )

    except GeminiToolError as e:
        logger.error("Gemini extraction failed: %s", e)
        details["confirmed"] = False

    except Exception as e:
        logger.error("Gemini extraction failed with unexpected error: %s", e)
        details["confirmed"] = False

    return details


def _extract_slot_index_from_ordinals(text: str, slot_count: int) -> int | None:
    for index, phrases in _ORDINAL_PATTERNS:
        if index >= slot_count:
            continue
        if any(phrase in text for phrase in phrases):
            return index

    match = re.search(r"\b(?:choose|chose|selected|confirm|confirmed|take|taking|works|work with)\s+(?:the\s+)?(first|second|third|1st|2nd|3rd|one|two|three|1|2|3)\b", text)
    if not match:
        return None

    token = match.group(1)
    mapping = {
        "first": 0,
        "1st": 0,
        "one": 0,
        "1": 0,
        "second": 1,
        "2nd": 1,
        "two": 1,
        "2": 1,
        "third": 2,
        "3rd": 2,
        "three": 2,
        "3": 2,
    }
    index = mapping.get(token)
    return index if index is not None and index < slot_count else None


def _extract_slot_index_from_datetime_match(text: str, time_slots: list[Any]) -> int | None:
    normalized_text = _normalize_datetime_text(text)
    unique_dates = {
        _normalize_date_phrase(str(slot.get("date", "")).lower().strip()): 0
        for slot in time_slots
        if str(slot.get("date", "")).strip()
    }
    for slot in time_slots:
        normalized_date = _normalize_date_phrase(str(slot.get("date", "")).lower().strip())
        if normalized_date:
            unique_dates[normalized_date] = unique_dates.get(normalized_date, 0) + 1

    exact_matches: list[int] = []
    time_only_matches: list[int] = []
    unique_date_matches: list[int] = []

    for slot_idx, slot in enumerate(time_slots):
        slot_date = _normalize_date_phrase(str(slot.get("date", "")).lower().strip())
        slot_time = _normalize_time_phrase(str(slot.get("time", "")).lower().strip())

        if slot_date and slot_time and slot_date in normalized_text and slot_time in normalized_text:
            exact_matches.append(slot_idx)
        elif slot_time and slot_time in normalized_text:
            time_only_matches.append(slot_idx)
        elif slot_date and unique_dates.get(slot_date) == 1 and slot_date in normalized_text:
            unique_date_matches.append(slot_idx)

    if exact_matches:
        return exact_matches[-1]
    if time_only_matches:
        return time_only_matches[-1]
    if unique_date_matches:
        return unique_date_matches[-1]
    return None


def _normalize_datetime_text(text: str) -> str:
    normalized = text.lower()
    normalized = normalized.replace("a.m.", "am").replace("p.m.", "pm")
    normalized = re.sub(r"\b(\d{1,2})\s*:\s*00\s*(am|pm)\b", r"\1 \2", normalized)
    normalized = re.sub(r"\b(\d{1,2})\s*(am|pm)\b", r"\1:00 \2", normalized)
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return normalized


def _normalize_time_phrase(value: str) -> str:
    raw = value.strip().lower().replace("a.m.", "am").replace("p.m.", "pm")
    if not raw:
        return raw

    for fmt in ("%I:%M %p", "%I %p", "%H:%M"):
        try:
            parsed = datetime.strptime(raw, fmt)
            return parsed.strftime("%I:%M %p").lstrip("0").lower()
        except ValueError:
            continue

    match = re.search(r"\b(\d{1,2})\s*(am|pm)\b", raw)
    if match:
        return f"{int(match.group(1))}:00 {match.group(2)}"

    return raw


def _normalize_date_phrase(value: str) -> str:
    raw = value.strip().lower()
    if not raw:
        return raw

    raw = re.sub(r"(\d+)(st|nd|rd|th)\b", r"\1", raw)
    raw = re.sub(r"\s+", " ", raw).strip()
    return raw


class CallSchedulingAgent(BaseADKAgent):
    def __init__(self) -> None:
        super().__init__(
            key="call_scheduling_agent",
            instruction=(
                "You are a healthcare appointment scheduling assistant. When given patient details and available time slots, "
                "you will orchestrate outbound phone calls via Vapi to schedule a medical appointment. "
                "Follow these steps exactly: "
                "STEP 1 - For each available time slot provided by the frontend: "
                "  a) Call make_appointment_call with the patient details and time slot. If status is error, try next slot. "
                "  b) Call wait_for_call_completion with the call_id. Block until call ends. "
                "  c) Call get_call_transcript with the call_id. "
                "  d) Read the transcript and extract: confirmation status, date/time, doctor name, location/department. "
                "  e) If confirmed, STOP and return the result. If NOT confirmed, try the next time slot. "
                "STEP 2 - If all time slots are exhausted with no confirmation, return status: no_availability. "
                "STEP 3 - Return the final JSON with status, all call_ids, attempted_slots, and confirmed_appointment (if any)."
            ),
            tools={"schedule_appointment_tool": schedule_appointment_with_vapi},
        )

    def process(self, message: AgentMessage, envelope: A2AEnvelope) -> AgentMessage:
        try:
            result = self.call_tool("schedule_appointment_tool", message)
            message.metadata["appointment_result"] = result
            logger.info("Appointment scheduling completed: %s", result.get("status"))
        except Exception as exc:
            logger.error("Appointment scheduling failed: %s", exc)
            message.metadata["appointment_result"] = {
                "status": "failed",
                "error": str(exc),
            }

        return message
