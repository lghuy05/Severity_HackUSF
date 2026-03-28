from pathlib import Path
import sys
import os
from typing import Any
from datetime import datetime, timezone

import google.generativeai as genai
from fastapi import FastAPI
from fastapi import File
from fastapi import Form
from fastapi import HTTPException
from fastapi import UploadFile
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
from backend.llm_agents import generate_summary_report
from backend.memory import add_message, get_history, get_history_context, get_medical_history, set_medical_history
from backend.models import ChatRequest, EmergencyPayload, FacilityTransmitPayload
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


@app.post("/api/upload-records")
async def upload_records(
    session_id: str = Form(...),
    file: UploadFile = File(...),
):
    if not session_id.strip():
        raise HTTPException(status_code=400, detail="session_id must not be empty")

    content_type = file.content_type or "application/octet-stream"
    if content_type not in {"application/pdf", "image/png", "image/jpeg", "image/jpg", "image/webp"}:
        raise HTTPException(status_code=400, detail="Unsupported file type. Use PDF or image formats.")

    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    extracted_text = ""
    if GOOGLE_API_KEY:
        model = genai.GenerativeModel("gemini-1.5-flash")
        prompt = "Extract all relevant medical history, allergies, and past diagnoses from this document."
        try:
            response = await model.generate_content_async(
                [
                    prompt,
                    {
                        "mime_type": content_type,
                        "data": file_bytes,
                    },
                ]
            )
            extracted_text = (getattr(response, "text", "") or "").strip()
        except Exception as exc:
            raise HTTPException(status_code=502, detail=f"Failed to extract records: {exc}") from exc
    else:
        extracted_text = "GOOGLE_API_KEY missing. Could not process document with Gemini."

    set_medical_history(session_id, extracted_text)
    return {"status": "success", "extracted_data": extracted_text}


@app.post("/api/facility/transmit")
def transmit_to_facility(payload: FacilityTransmitPayload):
    print("\n" + "=" * 70)
    print("🏥 MOCK TRANSMISSION TO FACILITY SUCCESSFUL 🏥")
    print(f"session_id: {payload.session_id}")
    print(f"hospital_id: {payload.hospital_id}")
    print("=" * 70 + "\n")
    return {
        "status": "transmitted",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/api/report/{session_id}")
async def get_session_report(session_id: str):
    history = get_history(session_id)
    if not history:
        raise HTTPException(status_code=404, detail="No conversation history found for this session")

    history_str = get_history_context(session_id, limit=max(len(history), 1))
    medical_history = get_medical_history(session_id)
    report_input = history_str
    if medical_history:
        report_input = f"{history_str}\n\nmedical_history: {medical_history}"

    report = await generate_summary_report(report_input)
    return report


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
                target_language=chat_request.target_language,
            ):
                await websocket.send_json(event)
                if event.get("type") == "final":
                    final_response_text = str(event.get("response", ""))

            if final_response_text:
                add_message(chat_request.session_id, "assistant", final_response_text)

    except WebSocketDisconnect:
        return
