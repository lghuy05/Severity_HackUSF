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
        user_id="patient-123",
        location="Tampa, Florida",
        raw_text="I have chest pain and need an appointment",
        preferred_language="en",
        normalized_text="I have chest pain and need an appointment",
        detected_language="en",
        translated_text="I have chest pain and need an appointment",
        risk_level="high",
        risk_reason="Chest pain is a high-risk symptom",
        hospitals=[hospital],
        metadata={
            "patient_name": "John Smith",
            "preferred_date": "Next Monday",
            "preferred_time": "2:00 PM",
            "reason_for_visit": "Chest pain evaluation",
            "hospital_name": "Mercy General Hospital",
            "max_wait_seconds": 60,
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
    print(f"  Risk Level: {message.risk_level}")

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
            print(f"\nStatus: {result.get('status')}")
            print(f"Call ID: {result.get('call_id')}")

            if "appointment" in result:
                appt = result["appointment"]
                print(f"\nAppointment Details:")
                print(f"  Patient: {appt.get('patient_name')}")
                print(f"  Hospital: {appt.get('hospital')}")
                print(f"  Date: {appt.get('date')}")
                print(f"  Time: {appt.get('time')}")
                print(f"  Doctor: {appt.get('doctor')}")
                print(f"  Location: {appt.get('location')}")
                print(f"  Instructions: {appt.get('instructions')}")

            if result.get("transcript"):
                print(f"\nTranscript:")
                print(f"  {result['transcript'][:300]}...")

            if result.get("error"):
                print(f"\nError: {result['error']}")

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
