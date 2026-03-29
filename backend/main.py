import json
from pathlib import Path
import sys

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from backend.logging_config import configure_logging
from backend.orchestrator import get_chat_session, run_analysis, run_chat_turn, run_communication, stream_chat_turn
from backend.schemas import AnalyzeRequest, AnalyzeResponse, ChatSessionState, ChatTurnRequest, ChatTurnResponse, CommunicationRequest, CommunicationResponse

configure_logging()

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
        return ChatSessionState(session_id=session_id, location="", profile={"language": "en", "location": ""})
    return session
