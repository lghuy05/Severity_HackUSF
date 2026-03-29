import json
from pathlib import Path
import sys

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

load_dotenv(ROOT / ".env")

from backend.logging_config import configure_logging
from backend.firebase import firebase_backend_ready
from backend.orchestrator import get_chat_session, run_analysis, run_chat_turn, run_communication, stream_chat_turn
from backend.schemas import AnalyzeRequest, AnalyzeResponse, ChatSessionState, ChatTurnRequest, ChatTurnResponse, CommunicationRequest, CommunicationResponse
from backend.user_profile_router import router as user_profile_router
from backend.visit_assistant import router as visit_assistant_router

configure_logging()

app = FastAPI(title="Health Equity Bridge API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(visit_assistant_router)
app.include_router(user_profile_router)


@app.get("/health")
def health():
    return {"status": "ok", "firebase_ready": firebase_backend_ready()}


@app.post("/analyze", response_model=AnalyzeResponse)
def analyze(request: AnalyzeRequest):
    return run_analysis(request)


@app.post("/communicate", response_model=CommunicationResponse)
def communicate(request: CommunicationRequest):
    return run_communication(request.summary)


@app.post("/chat", response_model=ChatTurnResponse)
def chat(request: ChatTurnRequest):
    return run_chat_turn(request)


@app.post("/chat/stream")
def chat_stream(request: ChatTurnRequest):
    def event_stream():
        for chunk in stream_chat_turn(request):
            yield chunk.model_dump_json() + "\n"

    return StreamingResponse(event_stream(), media_type="application/x-ndjson")


@app.get("/chat/session/{session_id}", response_model=ChatSessionState)
def chat_session(session_id: str):
    session = get_chat_session(session_id)
    if session is None:
        return ChatSessionState(session_id=session_id, location="", profile={"name": "User", "language": "en", "location": ""})
    return session
