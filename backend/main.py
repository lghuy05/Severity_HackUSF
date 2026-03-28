from pathlib import Path
import sys
from threading import Lock
from typing import Any

from fastapi import FastAPI
from fastapi import WebSocket
from fastapi import WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pydantic import ValidationError

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from backend.orchestrator import run_analysis, run_communication, stream_mock_orchestrator
from shared.schemas import AnalyzeRequest, AnalyzeResponse, CommunicationRequest, CommunicationResponse


class ChatRequest(BaseModel):
    session_id: str
    message: str


class InMemorySessionStore:
    def __init__(self) -> None:
        self._data: dict[str, list[dict[str, str]]] = {}
        self._lock = Lock()

    def add_message(self, session_id: str, role: str, content: str) -> None:
        with self._lock:
            self._data.setdefault(session_id, []).append({"role": role, "content": content})

    def get_history(self, session_id: str) -> list[dict[str, str]]:
        with self._lock:
            return list(self._data.get(session_id, []))

    def clear_session(self, session_id: str) -> None:
        with self._lock:
            self._data.pop(session_id, None)


def add_message(session_id: str, role: str, content: str) -> None:
    session_store.add_message(session_id, role, content)


def get_history(session_id: str) -> list[dict[str, str]]:
    return session_store.get_history(session_id)


def clear_session(session_id: str) -> None:
    session_store.clear_session(session_id)

app = FastAPI(title="Health Equity Bridge API", version="0.1.0")
session_store = InMemorySessionStore()

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

            session_store.add_message(chat_request.session_id, "user", chat_request.message)
            history = session_store.get_history(chat_request.session_id)

            final_response_text = ""
            async for event in stream_mock_orchestrator(
                session_id=chat_request.session_id,
                user_message=chat_request.message,
                history=history,
            ):
                await websocket.send_json(event)
                if event.get("type") == "final":
                    final_response_text = str(event.get("response", ""))

            if final_response_text:
                session_store.add_message(chat_request.session_id, "assistant", final_response_text)

    except WebSocketDisconnect:
        return
