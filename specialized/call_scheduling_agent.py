from __future__ import annotations

import json
import logging
import os
import re
import time
from typing import Any

import requests

from agents.message_types import A2AEnvelope
from backend.schemas import AgentMessage
from core.base_agent import BaseADKAgent


logger = logging.getLogger(__name__)

VAPI_API_KEY = os.environ.get("VAPI_API_KEY", "")
VAPI_ASSISTANT_ID = os.environ.get("VAPI_ASSISTANT_ID", "")
VAPI_PHONE_NUMBER_ID = os.environ.get("VAPI_PHONE_NUMBER_ID", "")
VAPI_TO_NUMBER = os.environ.get("VAPI_TO_NUMBER", "")
VAPI_BASE_URL = "https://api.vapi.ai"





def make_appointment_call(message: AgentMessage) -> dict[str, Any]:
    """
    STEP 1: Make an outbound phone call via Vapi to schedule an appointment.
    
    Handles up to 3 time slots in a single call. If the first is rejected,
    the assistant automatically offers the second, then the third.
    
    Extracts patient details and time slots from message metadata.
    Returns: { "call_id": "...", "status": "...", "message": "..." }
    """
    patient_name = str(message.metadata.get("patient_name", "Unknown Patient")).strip()
    reason_for_visit = str(message.metadata.get("reason_for_visit", "Medical consultation")).strip()
    hospital_name = (
        str(message.metadata.get("hospital_name", ""))
        or (message.hospitals[0].name if message.hospitals else "Healthcare Facility")
    ).strip()
    
    # Get time slots - can be a list of dicts or fall back to single preferred date/time
    time_slots = message.metadata.get("time_slots")
    
    # Fallback: if no time_slots list, create one from preferred_date and preferred_time
    if not time_slots:
        preferred_date = str(message.metadata.get("preferred_date", "")).strip()
        preferred_time = str(message.metadata.get("preferred_time", "")).strip()
        if preferred_date or preferred_time:
            time_slots = [{"date": preferred_date, "time": preferred_time}]
    
    if not time_slots:
        logger.error("No time slots provided")
        return {"call_id": "", "status": "error", "message": "No time slots provided"}
    
    # Ensure we have at most 3 slots
    time_slots = time_slots[:3]
    logger.info(f"Scheduling with {len(time_slots)} time slot(s): {time_slots}")
    
    # Format time slots as variables for the Vapi assistant
    slots_list = []
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

    logger.debug(f"Vapi request - API key present: {bool(VAPI_API_KEY)}, API key length: {len(VAPI_API_KEY)}")
    logger.debug(f"Vapi request - Assistant ID: {VAPI_ASSISTANT_ID}, Phone Number ID: {VAPI_PHONE_NUMBER_ID}")
    logger.debug(f"Available slots for call: {available_slots}")

    try:
        response = requests.post(f"{VAPI_BASE_URL}/call/phone", json=payload, headers=headers, timeout=30)

        if response.status_code in (200, 201):
            data = response.json()
            call_id = data.get("id", "")
            logger.info(f"Vapi call initiated with {len(time_slots)} time slot(s): call_id={call_id}")
            return {"call_id": call_id, "status": "initiated", "message": "Call queued with Vapi", "num_slots": len(time_slots)}
        else:
            logger.error(f"Vapi error {response.status_code}: {response.text}")
            if response.status_code == 401:
                logger.error(f"Authentication failed. Verify your VAPI_API_KEY is correct.")
                logger.error(f"API Key used (first 20 chars): {VAPI_API_KEY[:20] if VAPI_API_KEY else 'NOT SET'}")
            return {"call_id": "", "status": "error", "message": f"Vapi {response.status_code}: {response.text}"}

    except Exception as e:
        logger.error(f"Exception calling Vapi: {e}")
        return {"call_id": "", "status": "error", "message": f"Exception: {str(e)}"}


def get_call_status(call_id: str) -> dict[str, Any]:
    """
    Get the current status of a Vapi call.
    Returns: { "call_id": "...", "status": "...", "ended_reason": "..." }
    """
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
        else:
            logger.error(f"get_call_status failed: {response.status_code} - {response.text}")
            return {"call_id": call_id, "status": "error", "ended_reason": response.text}

    except Exception as e:
        logger.error(f"Exception in get_call_status: {e}")
        return {"call_id": call_id, "status": "error", "ended_reason": str(e)}


def get_call_transcript(call_id: str) -> dict[str, Any]:
    """
    Retrieve the transcript and recording of a completed Vapi call.
    Returns: { "call_id": "...", "transcript": "...", "recording_url": "...", "duration_seconds": ... }
    """
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
            transcript_lines = []
            for msg in messages:
                role = msg.get("role", "unknown")
                content = msg.get("message", "")
                if content:
                    transcript_lines.append(f"{role}: {content}")

            transcript = "\n".join(transcript_lines)
            recording_url = data.get("recordingUrl", "")

            return {
                "call_id": call_id,
                "transcript": transcript,
                "recording_url": recording_url or "",
                "duration_seconds": 0,
            }
        else:
            logger.error(f"get_call_transcript failed: {response.status_code}")
            return {
                "call_id": call_id,
                "transcript": "",
                "recording_url": "",
                "duration_seconds": 0,
            }

    except Exception as e:
        logger.error(f"Exception in get_call_transcript: {e}")
        return {
            "call_id": call_id,
            "transcript": "",
            "recording_url": "",
            "duration_seconds": 0,
        }


def wait_for_call_completion(call_id: str, max_wait_seconds: int = 120, poll_interval: int = 5) -> dict[str, Any]:
    """
    STEP 2: Poll Vapi until call status is "ended" or timeout is reached.
    Returns: { "call_id": "...", "status": "...", "ended_reason": "..." }
    """
    if not call_id:
        return {"call_id": "", "status": "error", "ended_reason": "No call_id provided"}

    start_time = time.time()
    while True:
        elapsed = time.time() - start_time
        if elapsed > max_wait_seconds:
            logger.warning(f"Call {call_id} timeout after {elapsed:.1f}s")
            return {"call_id": call_id, "status": "timeout", "ended_reason": "Max wait time exceeded"}

        status_result = get_call_status(call_id)
        current_status = status_result.get("status", "")

        if current_status == "ended":
            logger.info(f"Call {call_id} completed with reason: {status_result.get('ended_reason')}")
            return status_result

        if current_status == "error":
            return status_result

        logger.info(f"Call {call_id} status: {current_status}, elapsed: {elapsed:.1f}s")
        time.sleep(poll_interval)


def schedule_appointment_with_vapi(message: AgentMessage) -> dict[str, Any]:
    """
    Main orchestration function: Make ONE phone call with up to 3 time slots.
    
    The Vapi assistant will:
    1. Offer the first time slot
    2. If rejected, offer the second slot
    3. If rejected, offer the third slot
    4. If any is confirmed, extract details and return
    5. If all rejected, return "failed" status
    """
    patient_name = str(message.metadata.get("patient_name", "Unknown Patient")).strip()
    hospital_name = (
        str(message.metadata.get("hospital_name", ""))
        or (message.hospitals[0].name if message.hospitals else "Healthcare Facility")
    ).strip()
    reason_for_visit = str(message.metadata.get("reason_for_visit", "Medical consultation")).strip()
    
    # Get the time slots
    time_slots = message.metadata.get("time_slots")
    
    # Fallback: if no time_slots list, create one from preferred_date and preferred_time
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

    logger.info(f"Starting appointment scheduling for {patient_name}")
    logger.info(f"Available time slots: {time_slots}")

    # STEP 1: Make the single call with all time slots
    logger.info(f"STEP 1: Making single call with {len(time_slots)} time slot(s)")
    call_result = make_appointment_call(message)

    if call_result["status"] == "error":
        logger.error(f"STEP 1 failed: {call_result['message']}")
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
    logger.info(f"STEP 1 complete: call_id={call_id}")

    # STEP 2: Wait for call to complete
    logger.info(f"STEP 2: Waiting for call {call_id} to complete (max {max_wait_seconds}s)")
    wait_result = wait_for_call_completion(call_id, max_wait_seconds, poll_interval)

    if wait_result["status"] in ["error", "timeout"]:
        logger.warning(f"STEP 2 failed: {wait_result['ended_reason']}")
        return {
            "status": "failed",
            "call_id": call_id,
            "appointment": None,
            "slots_tried": time_slots,
            "transcript": "",
            "recording_url": "",
            "error": f"Call did not complete: {wait_result['ended_reason']}",
        }

    logger.info(f"STEP 2 complete: call ended")

    # STEP 3: Get transcript
    logger.info(f"STEP 3: Retrieving transcript for call {call_id}")
    transcript_result = get_call_transcript(call_id)
    transcript = transcript_result.get("transcript", "")
    recording_url = transcript_result.get("recording_url", "")
    logger.info(f"STEP 3 complete: transcript length={len(transcript)}")

    # STEP 4: Extract appointment details
    logger.info(f"STEP 4: Extracting appointment details from transcript")
    appointment_details = _extract_appointment_details(transcript, patient_name, hospital_name, time_slots)
    logger.info(f"STEP 4 complete: confirmed={appointment_details['confirmed']}, slot_index={appointment_details['slot_index']}")

    # STEP 5: Build final response
    logger.info(f"STEP 5: Building final response")
    
    if appointment_details["confirmed"] and appointment_details["slot_index"] is not None:
        final_status = "confirmed"
        logger.info(f"🎉 APPOINTMENT CONFIRMED for slot {appointment_details['slot_index']}")
    else:
        final_status = "failed"
        logger.info(f"No time slots were confirmed")

    result = {
        "status": final_status,
        "call_id": call_id,
        "appointment": appointment_details,
        "slots_tried": time_slots,
        "transcript": transcript,
        "recording_url": recording_url,
    }

    logger.info(f"Appointment scheduling workflow complete: status={final_status}")
    return result


def _extract_appointment_details(transcript: str, patient_name: str, hospital_name: str, time_slots: list) -> dict[str, Any]:
    """
    STEP 4: Parse transcript to extract confirmation status and appointment details.
    Determines which slot (0, 1, or 2) was confirmed, if any.
    Never fabricate details. Use None for missing fields.
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
        return details

    transcript_lower = transcript.lower()

    # Check if appointment was confirmed
    # Look for EXPLICIT confirmation phrases that the Vapi assistant says
    confirmation_phrases = [
        "the appointment is confirmed",
        "appointment is confirmed",
        "we have you scheduled",
        "your appointment is confirmed",
        "you're scheduled for",
        "you're all set",
    ]
    
    is_confirmed = False
    for phrase in confirmation_phrases:
        if phrase in transcript_lower:
            is_confirmed = True
            logger.debug(f"Confirmation detected: found '{phrase}' in transcript")
            break
    
    # Also reject if we hear explicit rejection phrases
    rejection_phrases = [
        "not available",
        "unavailable",
        "can't schedule",
        "no availability",
        "unable to book",
        "unfortunately",
    ]
    
    if not is_confirmed:
        for phrase in rejection_phrases:
            if phrase in transcript_lower:
                logger.debug(f"Rejection detected: found '{phrase}' in transcript")
                break

    details["confirmed"] = is_confirmed
    
    # Determine which slot was confirmed by checking which slot details appear in transcript
    if is_confirmed and time_slots:
        for slot_idx, slot in enumerate(time_slots):
            slot_date = str(slot.get("date", "")).lower().strip()
            slot_time = str(slot.get("time", "")).lower().strip()
            
            # Check if this slot's date AND time both appear in transcript
            # This is more reliable than checking individually
            if slot_date and slot_time:
                date_match = slot_date in transcript_lower
                time_match = slot_time in transcript_lower
                
                # If both date and time are found, this is likely the confirmed slot
                if date_match and time_match:
                    details["slot_index"] = slot_idx
                    details["date"] = slot.get("date")  # Use the actual slot date, not extracted
                    details["time"] = slot.get("time")  # Use the actual slot time, not extracted
                    logger.info(f"Slot {slot_idx} CONFIRMED: {slot_date} at {slot_time}")
                    break
            elif slot_date:
                # If only date is available, match on that
                if slot_date in transcript_lower:
                    details["slot_index"] = slot_idx
                    details["date"] = slot.get("date")
                    details["time"] = slot.get("time")
                    logger.info(f"Slot {slot_idx} matched by date: {slot_date}")
                    break
            elif slot_time:
                # If only time is available, match on that
                if slot_time in transcript_lower:
                    details["slot_index"] = slot_idx
                    details["date"] = slot.get("date")
                    details["time"] = slot.get("time")
                    logger.info(f"Slot {slot_idx} matched by time: {slot_time}")
                    break

    # Don't extract doctor, location, or instructions - focus on date/time only
    # Set them to None as per requirement

    return details


class CallSchedulingAgent(BaseADKAgent):
    """
    Google ADK agent that schedules medical appointments via Vapi phone calls.
    
    Tries up to 3 available time slots provided by the frontend.
    Stops on first confirmation or returns no_availability if all slots are exhausted.
    
    Follows the multi-slot workflow:
    1. Get available time slots from message metadata
    2. For each time slot: Make outbound call to hospital
    3. Wait for call completion
    4. Retrieve transcript
    5. Extract appointment details and check for confirmation
    6. If confirmed → Return immediately (STOP trying other slots)
    7. If not confirmed → Try next slot
    8. If all slots exhausted → Return no_availability status
    """

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
        """
        Process appointment scheduling request with multiple time slots.
        Stores result in message.metadata under 'appointment_result'.
        """
        try:
            result = self.call_tool("schedule_appointment_tool", message)
            message.metadata["appointment_result"] = result
            logger.info(f"Appointment scheduling completed: {result.get('status')}")
        except Exception as e:
            logger.error(f"Appointment scheduling failed: {e}")
            message.metadata["appointment_result"] = {
                "status": "failed",
                "error": str(e),
            }

        return message
