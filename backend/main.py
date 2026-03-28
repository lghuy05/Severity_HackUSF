"""
Health Equity Bridge -- FastAPI Backend
=======================================
Full multi-agent medical triage backend with:
  - Live Gemini triage + Google Places APIs
  - Pricing estimation + Language translation
  - Medical record upload (multimodal LLM)
  - Facility transmission + Summary reports
"""

from datetime import datetime, timezone
from pathlib import Path
import json
import os
import re
import sys
import uuid

from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field
import google.generativeai as genai

# ---------------------------------------------------------------------------
# Load environment variables from frontend/.env.local  (shared API key)
# ---------------------------------------------------------------------------
_ENV_PATH = Path(__file__).resolve().parents[1] / "frontend" / ".env.local"
load_dotenv(_ENV_PATH)
print(f"[OK] Loaded env from {_ENV_PATH}  (GOOGLE_API_KEY={'set' if os.getenv('GOOGLE_API_KEY') else 'MISSING'})")

# ---------------------------------------------------------------------------
# Path setup -- keep the project root importable
# ---------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from backend.orchestrator import run_analysis, run_communication
from backend.session_manager import (
    add_message,
    get_history,
    clear_session,
    list_sessions,
    get_emergency_context,
    set_medical_history,
    get_medical_history,
)
from backend.live_orchestrator import stream_orchestrator
from shared.schemas import (
    AnalyzeRequest,
    AnalyzeResponse,
    CommunicationRequest,
    CommunicationResponse,
)

# ---------------------------------------------------------------------------
# App & CORS
# ---------------------------------------------------------------------------
app = FastAPI(
    title="Health Equity Bridge API",
    version="0.4.0",
    description="Multi-agent medical triage backend -- full feature set",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------
class ChatRequest(BaseModel):
    """Incoming chat message from the frontend (SSE endpoint)."""
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    message: str
    latitude: float | None = None
    longitude: float | None = None
    target_language: str = "en"


class SessionInfo(BaseModel):
    session_id: str
    message_count: int


class EmergencyPayload(BaseModel):
    """Payload sent to the mock 911 dispatch receiver."""
    session_id: str
    extracted_symptoms: str
    urgency_level: str
    timestamp: datetime


class FacilityTransmitPayload(BaseModel):
    """Payload for mock facility transmission."""
    session_id: str
    hospital_id: str
    patient_data: dict


# ===================================================================
#  ORIGINAL ENDPOINTS
# ===================================================================

@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/analyze", response_model=AnalyzeResponse)
def analyze(request: AnalyzeRequest):
    return run_analysis(request)


@app.post("/communicate", response_model=CommunicationResponse)
def communicate(request: CommunicationRequest):
    return run_communication(request.summary)


# ===================================================================
#  SESSION MANAGEMENT ENDPOINTS
# ===================================================================

@app.get("/sessions", response_model=list[SessionInfo])
def get_sessions():
    """List all active chat sessions."""
    return [
        SessionInfo(session_id=sid, message_count=len(get_history(sid)))
        for sid in list_sessions()
    ]


@app.get("/sessions/{session_id}/history")
def get_session_history(session_id: str):
    """Return full conversation history for a session."""
    return {"session_id": session_id, "history": get_history(session_id)}


@app.delete("/sessions/{session_id}")
def delete_session(session_id: str):
    """Clear a chat session's history."""
    clear_session(session_id)
    return {"status": "cleared", "session_id": session_id}


# ===================================================================
#  EMERGENCY DISPATCH (mock 911 receiver)
# ===================================================================

@app.post("/api/emergency/dispatch")
def emergency_dispatch(payload: EmergencyPayload):
    """Mock 911 dispatch endpoint."""
    print("\n" + "=" * 60)
    print("!!!  MOCK 911 DISPATCH RECEIVED  !!!")
    print("=" * 60)
    print(f"  Session   : {payload.session_id}")
    print(f"  Urgency   : {payload.urgency_level}")
    print(f"  Timestamp : {payload.timestamp.isoformat()}")
    print(f"  Symptoms  : {payload.extracted_symptoms}")
    print("=" * 60 + "\n")

    return {
        "status": "Dispatched successfully",
        "session_id": payload.session_id,
        "urgency_level": payload.urgency_level,
    }


# ===================================================================
#  UPLOAD RECORDS  (multimodal LLM extraction)
# ===================================================================

@app.post("/api/upload-records")
async def upload_records(
    file: UploadFile = File(...),
    session_id: str = Form(...),
):
    """
    Accept an image or PDF upload, use Gemini to extract medical history,
    and store it in the session's medical_history key.
    """
    api_key = os.getenv("GOOGLE_API_KEY", "")
    if not api_key:
        return JSONResponse(
            status_code=500,
            content={"status": "error", "detail": "GOOGLE_API_KEY not configured"},
        )

    genai.configure(api_key=api_key)

    # Read the file bytes
    file_bytes = await file.read()
    content_type = file.content_type or "application/octet-stream"

    # Determine the MIME type for Gemini
    mime_type = content_type
    if "pdf" in content_type:
        mime_type = "application/pdf"
    elif "image" in content_type:
        mime_type = content_type  # image/png, image/jpeg, etc.

    try:
        model = genai.GenerativeModel(model_name="gemini-2.0-flash")
        response = await model.generate_content_async([
            "Extract all relevant medical history, allergies, medications, "
            "and past diagnoses from this document. "
            "Return a clear, structured summary.",
            {"mime_type": mime_type, "data": file_bytes},
        ])
        extracted = response.text.strip()

    except Exception as exc:
        return JSONResponse(
            status_code=500,
            content={"status": "error", "detail": f"Gemini extraction failed: {exc}"},
        )

    # Store in the session
    set_medical_history(session_id, extracted)

    # Also add as a system message in conversation history
    add_message(session_id, "system", f"[Medical Records Uploaded]\n{extracted}")

    return {
        "status": "success",
        "session_id": session_id,
        "filename": file.filename,
        "extracted_data": extracted,
    }


# ===================================================================
#  FACILITY TRANSMIT  (mock endpoint)
# ===================================================================

@app.post("/api/facility/transmit")
def facility_transmit(payload: FacilityTransmitPayload):
    """Mock facility transmission -- simulates sending patient data to a hospital."""
    ts = datetime.now(timezone.utc).isoformat()

    print("\n" + "=" * 60)
    print("[HOSPITAL] MOCK TRANSMISSION TO FACILITY SUCCESSFUL")
    print("=" * 60)
    print(f"  Session    : {payload.session_id}")
    print(f"  Hospital   : {payload.hospital_id}")
    print(f"  Timestamp  : {ts}")
    print(f"  Data keys  : {list(payload.patient_data.keys())}")
    print("=" * 60 + "\n")

    return {
        "status": "transmitted",
        "session_id": payload.session_id,
        "hospital_id": payload.hospital_id,
        "timestamp": ts,
    }


# ===================================================================
#  SUMMARY REPORT  (Gemini-powered)
# ===================================================================

def _extract_json_from_text(text: str) -> dict:
    """Robustly extract JSON from Gemini's response."""
    cleaned = re.sub(r"```(?:json)?\s*", "", text)
    cleaned = cleaned.strip().rstrip("`")
    match = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        return {"raw_summary": text[:500]}


@app.get("/api/report/{session_id}")
async def generate_report(session_id: str):
    """
    Generate a structured JSON medical report from the session's
    conversation history using Gemini as a Summary Agent.
    """
    history = get_history(session_id)
    if not history:
        return JSONResponse(
            status_code=404,
            content={"detail": f"No conversation found for session {session_id}"},
        )

    api_key = os.getenv("GOOGLE_API_KEY", "")
    if not api_key:
        return JSONResponse(
            status_code=500,
            content={"detail": "GOOGLE_API_KEY not configured"},
        )

    genai.configure(api_key=api_key)

    # Build conversation text
    convo_text = "\n".join(
        f"[{m['role']}] {m['content']}" for m in history
    )

    # Include medical records if available
    medical_history = get_medical_history(session_id)
    if medical_history:
        convo_text += f"\n\n[Uploaded Medical Records]\n{medical_history}"

    prompt = (
        "Generate a structured JSON medical report based on this triage conversation. "
        "Return ONLY valid JSON with exactly these keys:\n"
        "{\n"
        '  "patient_complaint": "...",\n'
        '  "triage_severity": "LOW | MEDIUM | HIGH | CRITICAL",\n'
        '  "recommended_actions": ["action1", "action2", ...],\n'
        '  "extracted_symptoms": ["symptom1", "symptom2", ...],\n'
        '  "medical_history_summary": "... or null if not available"\n'
        "}\n\n"
        f"Conversation:\n{convo_text}"
    )

    try:
        model = genai.GenerativeModel(model_name="gemini-2.0-flash")
        response = await model.generate_content_async(prompt)
        report = _extract_json_from_text(response.text)
        report["session_id"] = session_id
        report["generated_at"] = datetime.now(timezone.utc).isoformat()
        return report

    except Exception as exc:
        return JSONResponse(
            status_code=500,
            content={"detail": f"Report generation failed: {exc}"},
        )


# ===================================================================
#  WEBSOCKET  /chat  (preferred -- bi-directional)
# ===================================================================

@app.websocket("/chat")
async def websocket_chat(ws: WebSocket):
    """
    Bi-directional WebSocket chat.

    Client sends JSON:
        {"session_id": "...", "message": "...",
         "latitude": 28.06, "longitude": -82.41,
         "target_language": "es"}
    """
    await ws.accept()

    try:
        while True:
            data = await ws.receive_text()
            payload = json.loads(data)

            session_id = payload.get("session_id", str(uuid.uuid4()))
            user_message = payload.get("message", "")
            latitude = payload.get("latitude")
            longitude = payload.get("longitude")
            target_language = payload.get("target_language", "en")

            if not user_message:
                await ws.send_text(
                    json.dumps({"type": "error", "message": "Empty message"})
                )
                continue

            add_message(session_id, "user", user_message)
            history = get_history(session_id)

            final_response = None
            async for event_json in stream_orchestrator(
                session_id, user_message, history,
                latitude=latitude, longitude=longitude,
                target_language=target_language,
            ):
                await ws.send_text(event_json)
                event = json.loads(event_json)
                if event.get("type") == "final":
                    final_response = event.get("response", "")

            if final_response:
                add_message(session_id, "assistant", final_response)

    except WebSocketDisconnect:
        pass
    except Exception as exc:
        try:
            await ws.send_text(
                json.dumps({"type": "error", "message": str(exc)})
            )
        except Exception:
            pass


# ===================================================================
#  SSE  /chat/stream  (alternative -- works with plain fetch)
# ===================================================================

@app.post("/chat/stream")
async def sse_chat(request: ChatRequest):
    """
    Server-Sent Events streaming endpoint.

    Accepts JSON body with session_id, message, optional lat/lng,
    and target_language.
    """
    session_id = request.session_id
    user_message = request.message
    latitude = request.latitude
    longitude = request.longitude
    target_language = request.target_language

    add_message(session_id, "user", user_message)
    history = get_history(session_id)

    async def event_generator():
        final_response = None

        async for event_json in stream_orchestrator(
            session_id, user_message, history,
            latitude=latitude, longitude=longitude,
            target_language=target_language,
        ):
            yield f"data: {event_json}\n\n"
            event = json.loads(event_json)
            if event.get("type") == "final":
                final_response = event.get("response", "")

        if final_response:
            add_message(session_id, "assistant", final_response)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
