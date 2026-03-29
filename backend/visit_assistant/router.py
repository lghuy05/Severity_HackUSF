from __future__ import annotations

from fastapi import APIRouter, HTTPException

from tools.gemini_tool import GeminiToolError

from backend.visit_assistant.schemas import (
    VisitExtractNoteRequest,
    VisitExtractNoteResponse,
    VisitScheduleRequest,
    VisitScheduleResponse,
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
