#!/usr/bin/env python3
"""
Test script for CallSchedulingAgent with corrected Vapi API structure
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

try:
    from dotenv import load_dotenv
except ModuleNotFoundError:
    load_dotenv = None


ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))


def bootstrap_env() -> None:
    """Load environment variables from .env files BEFORE importing agents"""
    if load_dotenv is None:
        return

    for name in (".env", ".env.local"):
        env_path = ROOT / name
        if env_path.exists():
            load_dotenv(env_path, override=False)


# Load environment FIRST, before importing agent modules
bootstrap_env()

# Now import agents after environment is loaded
from agents.message_types import A2AEnvelope
from backend.schemas import AgentMessage, HospitalLocation
from specialized.call_scheduling_agent import CallSchedulingAgent


def create_test_message() -> AgentMessage:
    """Create a test AgentMessage with patient details"""
    hospital = HospitalLocation(
        name="Mercy General Hospital",
        address="1200 Market Street, Tampa, FL 33602",
        lat=27.9506,
        lng=-82.4508,
        phone="+18135550199",
    )

    message = AgentMessage(
        request_id="test-call-001",
        user_id="tomas-torrado",
        location="Tampa, Florida",
        raw_text="My stomach is hurting and I need an appointment",
        preferred_language="en",
        normalized_text="My stomach is hurting and I need an appointment",
        detected_language="en",
        translated_text="My stomach is hurting and I need an appointment",
        risk_level="medium",
        risk_reason="Stomach pain needs medical evaluation",
        hospitals=[hospital],
        metadata={
            "patient_name": "Tomas Torrado",
            "reason_for_visit": "Stomach pain evaluation",
            "hospital_name": "Mercy General Hospital",
            "time_slots": [
                {"date": "Monday April 7th", "time": "10:00 AM"},
                {"date": "Monday April 7th", "time": "2:00 PM"},
                {"date": "Tuesday April 8th", "time": "9:00 AM"},
            ],
            "max_wait_seconds": 180,
            "poll_interval": 5,
        },
    )

    return message


def test_call_scheduling_agent() -> None:
    """Test the CallSchedulingAgent"""
    print("\n" + "=" * 70)
    print("TESTING: CallSchedulingAgent (matching teammate's working code)")
    print("=" * 70)

    vapi_key = os.getenv("VAPI_API_KEY")
    vapi_assistant = os.getenv("VAPI_ASSISTANT_ID")
    vapi_phone = os.getenv("VAPI_PHONE_NUMBER_ID")
    vapi_to = os.getenv("VAPI_TO_NUMBER")

    print("\n✓ Environment Check:")
    print(f"  VAPI_API_KEY: {'✓ Set' if vapi_key else '✗ Missing'}")
    print(f"  VAPI_ASSISTANT_ID: {vapi_assistant or '✗ Missing'}")
    print(f"  VAPI_PHONE_NUMBER_ID: {vapi_phone or '✗ Missing'}")
    print(f"  VAPI_TO_NUMBER: {vapi_to or '✗ Missing'}")

    if not all([vapi_key, vapi_assistant, vapi_phone, vapi_to]):
        print("\n✗ Missing required environment variables!")
        return

    print("\n✓ Creating test message...")
    message = create_test_message()
    print(f"  Patient: {message.metadata.get('patient_name')}")
    print(f"  Hospital: {message.metadata.get('hospital_name')}")
    print(f"  Reason: {message.metadata.get('reason_for_visit')}")
    print(f"  Available slots:")
    for i, slot in enumerate(message.metadata.get('time_slots', []), 1):
        print(f"    {i}. {slot.get('time')} on {slot.get('date')}")

    print("\n✓ Initializing CallSchedulingAgent...")
    agent = CallSchedulingAgent()
    print(f"  Agent Key: {agent.key}")

    print("\n✓ Creating A2A envelope...")
    envelope = A2AEnvelope(
        from_agent="root_agent",
        to_agent="call_scheduling_agent",
        intent="schedule_appointment",
        request_id=message.request_id,
        payload=message.model_dump(mode="json"),
        metadata={"protocol": "A2A", "local": True},
    )

    print("\n✓ Running agent...")
    print("  (Making real Vapi call...)\n")

    try:
        result_message = agent.process(message, envelope)

        print("\n" + "=" * 70)
        print("RESULTS")
        print("=" * 70)

        if "appointment_result" in result_message.metadata:
            result = result_message.metadata["appointment_result"]
            print(f"\nOverall Status: {result.get('status')}")
            print(f"Call ID: {result.get('call_id')}")
            
            if result.get("slots_tried"):
                print(f"\nTime Slots Tried:")
                for i, slot in enumerate(result["slots_tried"], 1):
                    print(f"  {i}. {slot.get('time')} on {slot.get('date')}")

            if "appointment" in result and result["appointment"]:
                appt = result["appointment"]
                print(f"\n✅ APPOINTMENT DETAILS:")
                print(f"  Patient: {appt.get('patient_name')}")
                print(f"  Hospital: {appt.get('hospital')}")
                print(f"  Date: {appt.get('date')}")
                print(f"  Time: {appt.get('time')}")
                print(f"  Doctor: {appt.get('doctor')}")
                print(f"  Location: {appt.get('location')}")
                print(f"  Instructions: {appt.get('instructions')}")
                print(f"  Confirmed: {appt.get('confirmed')}")
                if appt.get('slot_index') is not None:
                    print(f"  Booked Slot: #{appt.get('slot_index') + 1}")

            if result.get("transcript"):
                print(f"\nTranscript Snippet:")
                print(f"  {result['transcript'][:400]}...")

            if result.get("error"):
                print(f"\n❌ Error: {result['error']}")

        print("\n" + "=" * 70)
        print("✓ Test completed!")
        print("=" * 70)

    except Exception as e:
        print("\n" + "=" * 70)
        print("✗ Test failed:")
        print("=" * 70)
        print(f"\n{type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_call_scheduling_agent()
