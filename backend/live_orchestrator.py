"""
Live orchestrator -- uses real Gemini triage + Google Places.

Replaces the mock normal-triage flow with actual API calls while keeping
the same streaming interface, emergency bypass logic, and event schema.
"""

import asyncio
import json
from datetime import datetime, timezone
from typing import AsyncGenerator, List, Optional

import httpx

from backend.session_manager import get_emergency_context
from agents.live_triage import run_triage
from agents.live_maps import get_nearby_hospitals

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
    """Simple keyword scan -- returns True if any distress phrase is found."""
    lower = message.lower()
    return any(kw in lower for kw in EMERGENCY_KEYWORDS)


# ===================================================================
#  Main streaming generator
# ===================================================================

async def stream_orchestrator(
    session_id: str,
    user_message: str,
    history: List[dict],
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
) -> AsyncGenerator[str, None]:
    """
    Async generator that yields newline-delimited JSON strings.

    The frontend should parse each line and react:
      - type == "status"  -> update the "thought process" UI
      - type == "final"   -> render the completed result card
    """

    # ------------------------------------------------------------------
    # EMERGENCY BYPASS  (keyword detection -> dispatch)
    # ------------------------------------------------------------------
    if _is_emergency(user_message):
        yield json.dumps({
            "type": "status",
            "status": "critical",
            "agent": "Triage Agent",
            "message": "CRITICAL severity detected. Escalating to Emergency Agent.",
        })
        await asyncio.sleep(0.4)

        context = get_emergency_context(session_id, limit=5)

        yield json.dumps({
            "type": "status",
            "status": "action",
            "agent": "Emergency Agent",
            "message": "Compiling emergency payload and contacting dispatch...",
        })
        await asyncio.sleep(0.3)

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
        await asyncio.sleep(0.3)

        yield json.dumps({
            "type": "final",
            "severity": "CRITICAL",
            "reason": "Emergency keywords detected in user message.",
            "response": (
                "Emergency services have been notified. "
                "Please stay calm and stay on the line. "
                "If you are in immediate danger, call 911 directly."
            ),
            "emergency_dispatched": True,
            "map_trigger": False,
            "emergency_flag": True,
            "hospitals": [],
        })
        return

    # ------------------------------------------------------------------
    # LIVE TRIAGE FLOW
    # ------------------------------------------------------------------

    # Step 1: Triage via Gemini
    yield json.dumps({
        "type": "status",
        "status": "processing",
        "agent": "Triage Agent",
        "message": "Analyzing symptoms with Gemini...",
    })

    # Build a compact history string for the LLM
    history_str = "\n".join(
        f"[{m['role']}] {m['content']}" for m in history[-5:]
    ) if history else "(no prior messages)"

    triage_result = await run_triage(user_message, history_str)

    severity = triage_result.get("severity", "MEDIUM")
    reason = triage_result.get("reason", "")
    response_text = triage_result.get("response_text", "")

    yield json.dumps({
        "type": "status",
        "status": "processing",
        "agent": "Triage Agent",
        "message": f"Severity classified as {severity}: {reason}",
    })

    # Step 2: Maps (only for HIGH/CRITICAL with location)
    hospitals = []

    if severity in ("HIGH", "CRITICAL") and latitude is not None and longitude is not None:
        yield json.dumps({
            "type": "status",
            "status": "processing",
            "agent": "Maps Agent",
            "message": "Checking location for nearby facilities...",
        })

        hospitals = await get_nearby_hospitals(latitude, longitude)

        yield json.dumps({
            "type": "status",
            "status": "processing",
            "agent": "Maps Agent",
            "message": f"Found {len(hospitals)} nearby hospital(s).",
        })
    elif severity in ("HIGH", "CRITICAL"):
        yield json.dumps({
            "type": "status",
            "status": "processing",
            "agent": "Maps Agent",
            "message": "No location provided -- skipping hospital search.",
        })
    else:
        yield json.dumps({
            "type": "status",
            "status": "processing",
            "agent": "Maps Agent",
            "message": "Severity is manageable -- hospital search not needed.",
        })

    # Step 3: Final response
    yield json.dumps({
        "type": "final",
        "severity": severity,
        "reason": reason,
        "response": response_text,
        "map_trigger": len(hospitals) > 0,
        "emergency_flag": severity == "CRITICAL",
        "emergency_dispatched": False,
        "hospitals": hospitals,
    })
