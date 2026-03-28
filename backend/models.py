from datetime import datetime

from pydantic import BaseModel


class ChatRequest(BaseModel):
    session_id: str
    message: str
    latitude: float | None = None
    longitude: float | None = None


class EmergencyPayload(BaseModel):
    session_id: str
    extracted_symptoms: str
    urgency_level: str
    timestamp: datetime