from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


VisitSeverity = Literal["low", "medium", "high", "unknown"]
VisitScheduleStatus = Literal["scheduled", "queued", "failed"]


class VisitExtractNoteRequest(BaseModel):
    transcript: str = Field(min_length=1)


class VisitStructuredNote(BaseModel):
    summary: str
    symptoms: list[str] = Field(default_factory=list)
    severity: VisitSeverity = "unknown"
    timeline: str
    action_items: list[str] = Field(default_factory=list)


class VisitExtractNoteResponse(BaseModel):
    note: VisitStructuredNote


class VisitSummarizeRequest(BaseModel):
    transcript: str = Field(min_length=1)


class VisitSummarizeResponse(BaseModel):
    summary: str


class VisitTranslateTurnRequest(BaseModel):
    text: str = Field(min_length=1)
    source_language: str = Field(min_length=2)
    target_language: str = Field(min_length=2)


class VisitTranslateTurnResponse(BaseModel):
    source_text: str
    translated_text: str
    source_language: str
    target_language: str


class VisitSavedNote(BaseModel):
    id: str
    title: str
    transcript: str
    summary: str
    structured_note: VisitStructuredNote
    created_at: str
    updated_at: str


class VisitSaveNoteRequest(BaseModel):
    title: str = Field(min_length=1)
    transcript: str = Field(min_length=1)
    summary: str = Field(min_length=1)
    structured_note: VisitStructuredNote


class VisitNotesResponse(BaseModel):
    notes: list[VisitSavedNote] = Field(default_factory=list)


class VisitUserProfile(BaseModel):
    full_name: str = ""
    phone_number: str = ""
    language: str = "en"
    location: str = ""
    age: int | None = None
    gender: str | None = None


class VisitScheduleRequest(BaseModel):
    note: VisitStructuredNote
    user_profile: VisitUserProfile


class VisitScheduleResponse(BaseModel):
    status: VisitScheduleStatus
    provider: str = "vapi"
    message: str
    external_call_id: str | None = None
    request_payload: dict[str, Any] = Field(default_factory=dict)
    raw_response: dict[str, Any] = Field(default_factory=dict)
