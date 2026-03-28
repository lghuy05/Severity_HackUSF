"""
Mock orchestrator – simulates the multi-agent thought process.

Replace this with the real Google ADK orchestrator once agents/ is ready.
Each `yield` is a JSON-serialisable dict streamed to the frontend in real time.

Features:
  • Normal triage flow  (language → triage → navigation → emergency check → final)
  • Emergency bypass     (keyword detection → dispatch to /api/emergency/dispatch)
"""

import asyncio
import json
from datetime import datetime, timezone
from typing import AsyncGenerator, List

import httpx

from backend.session_manager import get_emergency_context

# ---------------------------------------------------------------------------
# Distress keywords that trigger the emergency bypass
# ---------------------------------------------------------------------------
EMERGENCY_KEYWORDS = [
    "call 911",
    "help me",
    "heart attack",
    "can't breathe",
    "cannot breathe",
    "stroke",
    "choking",
    "bleeding out",
    "unconscious",
    "seizure",
    "overdose",
    "anaphylaxis",
    "suicide",
    "dying",
]

DISPATCH_URL = "http://localhost:8000/api/emergency/dispatch"


def _is_emergency(message: str) -> bool:
    """Simple keyword scan – returns True if any distress phrase is found."""
    lower = message.lower()
    return any(kw in lower for kw in EMERGENCY_KEYWORDS)


# ===================================================================
#  Main streaming generator
# ===================================================================

async def stream_orchestrator(
    session_id: str,
    user_message: str,
    history: List[dict],
) -> AsyncGenerator[str, None]:
    """
    Async generator that yields newline-delimited JSON strings.

    The frontend should parse each line and react:
      • type == "status"  → update the "thought process" UI
      • type == "final"   → render the completed result card

    If the user's message contains emergency distress keywords the
    orchestrator immediately escalates, compiles emergency context,
    POSTs to /api/emergency/dispatch, and yields a CRITICAL final.
    """

    # ------------------------------------------------------------------
    # 🚨 EMERGENCY BYPASS
    # ------------------------------------------------------------------
    if _is_emergency(user_message):
        # 1. Inform the frontend – critical severity detected
        yield json.dumps({
            "type": "status",
            "status": "critical",
            "agent": "Triage Agent",
            "message": "🚨 Critical severity detected. Escalating to Emergency Agent.",
        })
        await asyncio.sleep(0.6)

        # 2. Compile emergency context from recent conversation
        context = get_emergency_context(session_id, limit=5)

        yield json.dumps({
            "type": "status",
            "status": "action",
            "agent": "Emergency Agent",
            "message": "Compiling emergency payload and contacting dispatch…",
        })
        await asyncio.sleep(0.5)

        # 3. POST to our mock dispatch endpoint
        payload = {
            "session_id": session_id,
            "extracted_symptoms": context,
            "urgency_level": "CRITICAL",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        dispatch_status = "unknown"
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(DISPATCH_URL, json=payload, timeout=5.0)
                resp.raise_for_status()
                dispatch_status = resp.json().get("status", "sent")
        except Exception as exc:
            dispatch_status = f"failed ({exc})"

        yield json.dumps({
            "type": "status",
            "status": "action",
            "agent": "Emergency Agent",
            "message": f"Dispatch result: {dispatch_status}",
        })
        await asyncio.sleep(0.4)

        # 4. Final response – force frontend into emergency mode
        yield json.dumps({
            "type": "final",
            "severity": "CRITICAL",
            "response": (
                "🚨 Emergency services have been notified. "
                "Please stay calm and stay on the line. "
                "If you are in immediate danger, call 911 directly."
            ),
            "emergency_dispatched": True,
            "map_trigger": False,
            "emergency_flag": True,
        })
        return  # stop – no normal flow

    # ------------------------------------------------------------------
    # 🩺 NORMAL TRIAGE FLOW
    # ------------------------------------------------------------------
    steps = [
        {
            "type": "status",
            "agent": "system",
            "message": "Agent received message",
        },
        {
            "type": "status",
            "agent": "language",
            "message": "Detecting language & normalising input…",
        },
        {
            "type": "status",
            "agent": "triage",
            "message": "Evaluating severity…",
        },
        {
            "type": "status",
            "agent": "navigation",
            "message": "Fetching nearby clinics…",
        },
        {
            "type": "status",
            "agent": "emergency",
            "message": "Checking emergency protocols…",
        },
    ]

    # Stream each thinking step with a small delay
    for step in steps:
        yield json.dumps(step)
        await asyncio.sleep(0.8)

    # Produce the final response
    final = {
        "type": "final",
        "severity": "MEDIUM",
        "response": (
            "Based on your symptoms, I recommend visiting an urgent care clinic. "
            "I've found several nearby facilities for you."
        ),
        "map_trigger": True,
        "emergency_flag": False,
        "emergency_dispatched": False,
        "hospitals": [
            {
                "name": "Tampa General Hospital",
                "address": "1 Tampa General Cir, Tampa, FL 33606",
                "lat": 27.9396,
                "lng": -82.4572,
                "phone": "(813) 844-7000",
            },
            {
                "name": "AdventHealth Tampa",
                "address": "3100 E Fletcher Ave, Tampa, FL 33613",
                "lat": 28.0667,
                "lng": -82.4098,
                "phone": "(813) 971-6000",
            },
        ],
    }
    yield json.dumps(final)
