"""
Health Equity Bridge – FastAPI Backend
======================================
Serves both the original /analyze & /communicate endpoints
AND the new real-time streaming /chat (WebSocket) + /chat/stream (SSE) endpoints.
"""

from datetime import datetime
from pathlib import Path
import json
import sys
import uuid

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Path setup – keep the project root importable
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
)
from backend.mock_orchestrator import stream_orchestrator
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
    version="0.2.0",
    description="Multi-agent medical triage backend with real-time streaming",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Pydantic models for the chat system
# ---------------------------------------------------------------------------
class ChatRequest(BaseModel):
    """Incoming chat message from the frontend (used by the SSE endpoint)."""
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    message: str


class SessionInfo(BaseModel):
    session_id: str
    message_count: int


class EmergencyPayload(BaseModel):
    """Payload sent to the mock 911 dispatch receiver."""
    session_id: str
    extracted_symptoms: str
    urgency_level: str
    timestamp: datetime


# ===================================================================
#  ORIGINAL ENDPOINTS (unchanged)
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
    """
    Mock 911 dispatch endpoint.

    In production this would forward to a real emergency services API.
    For now it prints a loud console warning and returns confirmation.
    """
    print("\n" + "=" * 60)
    print("🚨🚨🚨  MOCK 911 DISPATCH RECEIVED  🚨🚨🚨")
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
#  WEBSOCKET  /chat  (preferred – bi-directional)
# ===================================================================

@app.websocket("/chat")
async def websocket_chat(ws: WebSocket):
    """
    Bi-directional WebSocket chat.

    Client sends JSON:
        {"session_id": "...", "message": "I have a headache"}

    Server streams back newline-delimited JSON events:
        {"type": "status", "agent": "triage", "message": "Evaluating…"}
        ...
        {"type": "final", "severity": "HIGH", ...}
    """
    await ws.accept()

    try:
        while True:
            # ---- receive user message ----
            data = await ws.receive_text()
            payload = json.loads(data)

            session_id = payload.get("session_id", str(uuid.uuid4()))
            user_message = payload.get("message", "")

            if not user_message:
                await ws.send_text(
                    json.dumps({"type": "error", "message": "Empty message"})
                )
                continue

            # ---- persist user message ----
            add_message(session_id, "user", user_message)
            history = get_history(session_id)

            # ---- stream agent thought process ----
            final_response = None

            async for event_json in stream_orchestrator(
                session_id, user_message, history
            ):
                await ws.send_text(event_json)
                event = json.loads(event_json)
                if event.get("type") == "final":
                    final_response = event.get("response", "")

            # ---- persist assistant response ----
            if final_response:
                add_message(session_id, "assistant", final_response)

    except WebSocketDisconnect:
        pass  # client disconnected – nothing to clean up
    except Exception as exc:
        # Try to inform the client before closing
        try:
            await ws.send_text(
                json.dumps({"type": "error", "message": str(exc)})
            )
        except Exception:
            pass


# ===================================================================
#  SSE  /chat/stream  (alternative – works with plain fetch)
# ===================================================================

@app.post("/chat/stream")
async def sse_chat(request: ChatRequest):
    """
    Server-Sent Events streaming endpoint.

    Accepts a JSON body with `session_id` and `message`.
    Returns a text/event-stream where each line is a JSON event.

    Usage (frontend):
        const res = await fetch('/chat/stream', { method: 'POST', body: ... });
        const reader = res.body.getReader();
    """
    session_id = request.session_id
    user_message = request.message

    # persist user message
    add_message(session_id, "user", user_message)
    history = get_history(session_id)

    async def event_generator():
        final_response = None

        async for event_json in stream_orchestrator(
            session_id, user_message, history
        ):
            # SSE format: "data: {json}\n\n"
            yield f"data: {event_json}\n\n"
            event = json.loads(event_json)
            if event.get("type") == "final":
                final_response = event.get("response", "")

        # persist assistant response
        if final_response:
            add_message(session_id, "assistant", final_response)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # disable nginx buffering if behind proxy
        },
    )
