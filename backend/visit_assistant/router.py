from __future__ import annotations

from fastapi import APIRouter, Header, HTTPException

from tools.gemini_tool import GeminiToolError

from backend.visit_assistant.note_store import list_visit_notes, save_visit_note
from backend.visit_assistant.schemas import (
    VisitExtractNoteRequest,
    VisitExtractNoteResponse,
    VisitNotesResponse,
    VisitScheduleRequest,
    VisitScheduleResponse,
    VisitSaveNoteRequest,
    VisitSavedNote,
    VisitSummarizeRequest,
    VisitSummarizeResponse,
    VisitTranslateTurnRequest,
    VisitTranslateTurnResponse,
)
from backend.visit_assistant.service import (
    VisitAssistantConfigError,
    VisitAssistantError,
    extract_note,
    schedule_appointment,
    summarize_conversation,
    translate_turn,
)


router = APIRouter(prefix="/visit", tags=["visit-assistant"])


def _require_user_id(x_user_id: str | None) -> str:
    user_id = (x_user_id or "").strip()
    if not user_id:
        raise HTTPException(status_code=400, detail="Missing x-user-id header")
    return user_id


@router.post("/extract-note", response_model=VisitExtractNoteResponse)
def extract_note_route(request: VisitExtractNoteRequest) -> VisitExtractNoteResponse:
    try:
        return extract_note(request.transcript)
    except GeminiToolError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except VisitAssistantError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/summarize", response_model=VisitSummarizeResponse)
def summarize_route(request: VisitSummarizeRequest) -> VisitSummarizeResponse:
    try:
        return summarize_conversation(request.transcript)
    except GeminiToolError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except VisitAssistantError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/translate-turn", response_model=VisitTranslateTurnResponse)
def translate_turn_route(request: VisitTranslateTurnRequest) -> VisitTranslateTurnResponse:
    try:
        return translate_turn(
            text=request.text,
            source_language=request.source_language,
            target_language=request.target_language,
        )
    except GeminiToolError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except VisitAssistantError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/schedule", response_model=VisitScheduleResponse)
def schedule_route(request: VisitScheduleRequest) -> VisitScheduleResponse:
    try:
        return schedule_appointment(request)
    except VisitAssistantConfigError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except VisitAssistantError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/notes", response_model=VisitNotesResponse)
def list_notes_route(x_user_id: str | None = Header(default=None, alias="x-user-id")) -> VisitNotesResponse:
    return VisitNotesResponse(notes=list_visit_notes(_require_user_id(x_user_id)))


@router.post("/notes", response_model=VisitSavedNote)
def save_note_route(
    request: VisitSaveNoteRequest,
    x_user_id: str | None = Header(default=None, alias="x-user-id"),
) -> VisitSavedNote:
    try:
        return save_visit_note(_require_user_id(x_user_id), request)
    except VisitAssistantError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
