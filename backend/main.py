from pathlib import Path
import sys
import os
from typing import Any

import google.generativeai as genai
from fastapi import FastAPI
from fastapi import WebSocket
from fastapi import WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import ValidationError
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)

from backend.orchestrator import run_analysis, run_communication, stream_mock_orchestrator
from backend.memory import add_message, get_history, get_history_context
from backend.models import ChatRequest, EmergencyPayload
from shared.schemas import AnalyzeRequest, AnalyzeResponse, CommunicationRequest, CommunicationResponse


app = FastAPI(title="Health Equity Bridge API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/analyze", response_model=AnalyzeResponse)
def analyze(request: AnalyzeRequest):
    return run_analysis(request)


@app.post("/communicate", response_model=CommunicationResponse)
def communicate(request: CommunicationRequest):
    return run_communication(request.summary)


@app.post("/api/emergency/dispatch")
def emergency_dispatch(payload: EmergencyPayload):
    print("\n" + "!" * 70)
    print("!!! MOCK 911 DISPATCH RECEIVED !!!")
    print(f"session_id: {payload.session_id}")
    print(f"urgency_level: {payload.urgency_level}")
    print(f"timestamp: {payload.timestamp.isoformat()}")
    print(f"extracted_symptoms: {payload.extracted_symptoms}")
    print("!" * 70 + "\n")
    return {"status": "Dispatched successfully"}


@app.websocket("/chat")
async def chat_socket(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            payload: Any = await websocket.receive_json()

            try:
                chat_request = ChatRequest.model_validate(payload)
            except ValidationError as exc:
                await websocket.send_json(
                    {
                        "type": "error",
                        "message": "Invalid payload. Expected {session_id, message}.",
                        "details": exc.errors(),
                    }
                )
                continue

            if not chat_request.session_id.strip():
                await websocket.send_json(
                    {
                        "type": "error",
                        "message": "session_id must not be empty",
                    }
                )
                continue

            add_message(chat_request.session_id, "user", chat_request.message)
            history = get_history(chat_request.session_id)
            history_str = get_history_context(chat_request.session_id, limit=8)

            final_response_text = ""
            async for event in stream_mock_orchestrator(
                session_id=chat_request.session_id,
                user_message=chat_request.message,
                history=history,
                history_str=history_str,
                latitude=chat_request.latitude,
                longitude=chat_request.longitude,
            ):
                await websocket.send_json(event)
                if event.get("type") == "final":
                    final_response_text = str(event.get("response", ""))

            if final_response_text:
                add_message(chat_request.session_id, "assistant", final_response_text)

    except WebSocketDisconnect:
        return
