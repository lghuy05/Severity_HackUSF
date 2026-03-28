from typing import List, Literal

from pydantic import BaseModel


RiskLevel = Literal["low", "medium", "high"]


class AnalyzeRequest(BaseModel):
    text: str
    location: str


class LanguageOutput(BaseModel):
    detected_language: str
    simplified_text: str
    translated_text: str


class TriageOutput(BaseModel):
    risk_level: RiskLevel
    explanation: str


class HospitalLocation(BaseModel):
    name: str
    address: str
    lat: float
    lng: float
    phone: str


class NavigationOutput(BaseModel):
    origin: str
    recommendation: str
    hospitals: List[HospitalLocation]


class EmergencyOutput(BaseModel):
    emergency_flag: bool
    instructions: List[str]


class SummaryOutput(BaseModel):
    patient_input: str
    location: str
    detected_language: str
    normalized_text: str
    risk_level: RiskLevel
    triage_explanation: str
    recommended_sites: List[str]
    emergency_flag: bool
    emergency_instructions: List[str]


class AnalyzeResponse(BaseModel):
    language_output: LanguageOutput
    triage: TriageOutput
    navigation: NavigationOutput
    summary: SummaryOutput
    provider_message: str
    emergency_flag: bool
    emergency: EmergencyOutput


class CommunicationRequest(BaseModel):
    summary: SummaryOutput


class CommunicationResponse(BaseModel):
    message: str
