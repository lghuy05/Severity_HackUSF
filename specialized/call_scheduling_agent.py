from __future__ import annotations

import json
import logging
import os
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
    
    Extracts patient details from message and calls Vapi /call/phone endpoint.
    Returns: { "call_id": "...", "status": "...", "message": "..." }
    """
    patient_name = str(message.metadata.get("patient_name", "Unknown Patient")).strip()
    preferred_date = str(message.metadata.get("preferred_date", "")).strip()
    preferred_time = str(message.metadata.get("preferred_time", "")).strip()
    reason_for_visit = str(message.metadata.get("reason_for_visit", "Medical consultation")).strip()
    hospital_name = (
        str(message.metadata.get("hospital_name", ""))
        or (message.hospitals[0].name if message.hospitals else "Healthcare Facility")
    ).strip()

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
                "preferred_date": preferred_date,
                "preferred_time": preferred_time,
                "reason_for_visit": reason_for_visit,
                "hospital_name": hospital_name,
            }
        },
    }

    headers = {
        "Authorization": VAPI_API_KEY,
        "Content-Type": "application/json",
    }

    # DEBUG: Log what we're about to send
    logger.debug(f"Vapi request - API key present: {bool(VAPI_API_KEY)}, API key length: {len(VAPI_API_KEY)}")
    logger.debug(f"Vapi request - Assistant ID: {VAPI_ASSISTANT_ID}, Phone Number ID: {VAPI_PHONE_NUMBER_ID}")

    try:
        response = requests.post(f"{VAPI_BASE_URL}/call/phone", json=payload, headers=headers, timeout=30)

        if response.status_code in (200, 201):
            data = response.json()
            call_id = data.get("id", "")
            logger.info(f"Vapi call initiated: call_id={call_id}")
            return {"call_id": call_id, "status": "initiated", "message": "Call queued with Vapi"}
        else:
            logger.error(f"Vapi error {response.status_code}: {response.text}")
            # Check if it's an auth error
            if response.status_code == 401:
                logger.error(f"Authentication failed. Verify your VAPI_API_KEY is correct.")
                logger.error(f"API Key used (first 20 chars): {VAPI_API_KEY[:20] if VAPI_API_KEY else 'NOT SET'}")
            return {"call_id": "", "status": "error", "message": f"Vapi {response.status_code}: {response.text}"}

    except Exception as e:
        logger.error(f"Exception calling Vapi: {e}")
        return {"call_id": "", "status": "error", "message": f"Exception: {str(e)}"}


def get_call_status(message: AgentMessage) -> dict[str, Any]:
    """
    Get the current status of a Vapi call.
    Returns: { "call_id": "...", "status": "...", "ended_reason": "..." }
    """
    call_id = str(message.metadata.get("call_id", "")).strip()
    if not call_id:
        return {"call_id": "", "status": "error", "ended_reason": "No call_id provided"}

    headers = {"Authorization": f"Bearer {VAPI_API_KEY}"}

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


def get_call_transcript(message: AgentMessage) -> dict[str, Any]:
    """
    Retrieve the transcript and recording of a completed Vapi call.
    Returns: { "call_id": "...", "transcript": "...", "recording_url": "...", "duration_seconds": ... }
    """
    call_id = str(message.metadata.get("call_id", "")).strip()
    if not call_id:
        return {
            "call_id": "",
            "transcript": "",
            "recording_url": "",
            "duration_seconds": 0,
        }

    headers = {"Authorization": f"Bearer {VAPI_API_KEY}"}

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
            duration = data.get("endedReason", "")

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


def wait_for_call_completion(message: AgentMessage) -> dict[str, Any]:
    """
    STEP 2: Poll Vapi until call status is "ended" or timeout is reached.
    Returns: { "call_id": "...", "status": "...", "ended_reason": "..." }
    """
    call_id = str(message.metadata.get("call_id", "")).strip()
    max_wait_seconds = int(message.metadata.get("max_wait_seconds", 300))
    poll_interval = int(message.metadata.get("poll_interval", 5))

    if not call_id:
        return {"call_id": "", "status": "error", "ended_reason": "No call_id provided"}

    start_time = time.time()
    while True:
        elapsed = time.time() - start_time
        if elapsed > max_wait_seconds:
            logger.warning(f"Call {call_id} timeout after {elapsed:.1f}s")
            return {"call_id": call_id, "status": "timeout", "ended_reason": "Max wait time exceeded"}

        status_result = get_call_status(message)
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
    Main orchestration function: Execute the 5-step appointment scheduling workflow.
    
    STEP 1: Call make_appointment_call
    STEP 2: Wait for call completion
    STEP 3: Get transcript
    STEP 4: Extract appointment details from transcript
    STEP 5: Return structured JSON
    """
    patient_name = str(message.metadata.get("patient_name", "Unknown Patient")).strip()
    hospital_name = (
        str(message.metadata.get("hospital_name", ""))
        or (message.hospitals[0].name if message.hospitals else "Healthcare Facility")
    ).strip()

    # STEP 1: Make the call
    logger.info(f"STEP 1: Initiating appointment call for {patient_name} at {hospital_name}")
    call_result = make_appointment_call(message)

    if call_result["status"] == "error":
        logger.error(f"STEP 1 failed: {call_result['message']}")
        return {
            "status": "failed",
            "call_id": "",
            "appointment": {
                "patient_name": patient_name,
                "hospital": hospital_name,
                "date": None,
                "time": None,
                "doctor": None,
                "location": None,
                "instructions": None,
            },
            "transcript": "",
            "recording_url": "",
            "error": call_result["message"],
        }

    call_id = call_result.get("call_id", "")
    message.metadata["call_id"] = call_id
    logger.info(f"STEP 1 complete: call_id={call_id}")

    # STEP 2: Wait for call to complete
    logger.info(f"STEP 2: Waiting for call {call_id} to complete (max 300s)")
    wait_result = wait_for_call_completion(message)

    if wait_result["status"] in ["error", "timeout"]:
        logger.error(f"STEP 2 failed: {wait_result['ended_reason']}")
        return {
            "status": "pending",
            "call_id": call_id,
            "appointment": {
                "patient_name": patient_name,
                "hospital": hospital_name,
                "date": None,
                "time": None,
                "doctor": None,
                "location": None,
                "instructions": None,
            },
            "transcript": "",
            "recording_url": "",
            "error": f"Call did not complete: {wait_result['ended_reason']}",
        }

    logger.info(f"STEP 2 complete: call ended with reason: {wait_result['ended_reason']}")

    # STEP 3: Get transcript
    logger.info(f"STEP 3: Retrieving transcript for call {call_id}")
    transcript_result = get_call_transcript(message)
    transcript = transcript_result.get("transcript", "")
    recording_url = transcript_result.get("recording_url", "")
    logger.info(f"STEP 3 complete: transcript length={len(transcript)}")

    # STEP 4: Extract appointment details from transcript
    logger.info(f"STEP 4: Extracting appointment details from transcript")
    appointment_details = _extract_appointment_details(transcript, patient_name, hospital_name)
    logger.info(f"STEP 4 complete: extracted details={appointment_details}")

    # STEP 5: Build final response
    logger.info(f"STEP 5: Building final response")
    final_status = "confirmed" if appointment_details["date"] and appointment_details["time"] else "pending"

    result = {
        "status": final_status,
        "call_id": call_id,
        "appointment": appointment_details,
        "transcript": transcript,
        "recording_url": recording_url,
    }

    logger.info(f"Appointment scheduling workflow complete: status={final_status}")
    return result


def _extract_appointment_details(transcript: str, patient_name: str, hospital_name: str) -> dict[str, Any]:
    """
    STEP 4: Parse transcript to extract confirmed date, time, doctor, location, instructions.
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
    }

    if not transcript:
        return details

    transcript_lower = transcript.lower()

    # Simple heuristic extraction (can be enhanced with LLM if needed)
    # Look for date patterns like "Monday", "tomorrow", "next Tuesday", or date formats
    date_keywords = [
        "monday",
        "tuesday",
        "wednesday",
        "thursday",
        "friday",
        "saturday",
        "sunday",
        "tomorrow",
        "next week",
    ]
    for keyword in date_keywords:
        if keyword in transcript_lower:
            details["date"] = keyword
            break

    # Look for time patterns like "10am", "2:30pm", "3 o'clock"
    import re

    time_pattern = r"\b([0-9]{1,2}):?([0-9]{2})?\s*(am|pm|AM|PM)?\b"
    time_match = re.search(time_pattern, transcript)
    if time_match:
        details["time"] = time_match.group(0)

    # Look for doctor name (simple heuristic: "Dr. ..." or "Doctor ...")
    doctor_pattern = r"(?:Dr\.|Doctor)\s+([A-Z][a-z]+)"
    doctor_match = re.search(doctor_pattern, transcript)
    if doctor_match:
        details["doctor"] = doctor_match.group(1)

    # Look for location/department keywords
    location_keywords = ["emergency", "pediatrics", "cardiology", "orthopedics", "urgent care", "clinic"]
    for keyword in location_keywords:
        if keyword in transcript_lower:
            details["location"] = keyword
            break

    # Look for special instructions
    instruction_keywords = ["bring", "fasting", "arrive early", "insurance", "paperwork"]
    instructions = []
    for keyword in instruction_keywords:
        if keyword in transcript_lower:
            instructions.append(f"Please {keyword} as mentioned during call")

    if instructions:
        details["instructions"] = " | ".join(instructions)

    return details


class CallSchedulingAgent(BaseADKAgent):
    """
    Google ADK agent that schedules medical appointments via Vapi phone calls.
    
    Follows the 5-step workflow:
    1. Make outbound call to hospital
    2. Wait for call completion
    3. Retrieve transcript
    4. Extract appointment details
    5. Return structured appointment confirmation
    """

    def __init__(self) -> None:
        super().__init__(
            key="call_scheduling_agent",
            instruction=(
                "You are a healthcare appointment scheduling assistant. When given patient details, "
                "you will orchestrate an outbound phone call via Vapi to schedule a medical appointment. "
                "Follow these steps exactly: "
                "STEP 1 - Call make_appointment_call with patient details. If status is error, stop and report. "
                "STEP 2 - Call wait_for_call_completion with the call_id. Block until call ends. "
                "STEP 3 - Call get_call_transcript with the call_id. "
                "STEP 4 - Read the transcript and extract: confirmed date/time, doctor name, location/department, "
                "special instructions. Never fabricate details. Use null for missing fields. "
                "STEP 5 - Return the final JSON with status, call_id, appointment details, transcript, and recording_url."
            ),
            tools={"schedule_appointment_tool": schedule_appointment_with_vapi},
        )

    def process(self, message: AgentMessage, envelope: A2AEnvelope) -> AgentMessage:
        """
        Process appointment scheduling request.
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
