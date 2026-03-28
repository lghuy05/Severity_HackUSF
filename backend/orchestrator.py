import json
import os
import re
from typing import Any, AsyncGenerator

import google.generativeai as genai
import httpx
from dotenv import load_dotenv

from agents.communication_agent import format_provider_message
from agents.emergency_agent import emergency_response
from agents.language_agent import process_language
from agents.navigation_agent import find_nearby_hospitals
from agents.summary_agent import build_summary
from agents.triage_agent import triage_symptoms
from shared.schemas import AnalyzeRequest, AnalyzeResponse, CommunicationResponse

load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)


def _extract_json_block(text: str) -> dict[str, Any]:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)

    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("No JSON object found in model response")

    return json.loads(cleaned[start : end + 1])


async def run_triage(user_message: str, history: str) -> dict[str, Any]:
    if not GOOGLE_API_KEY:
        return {
            "severity": "MEDIUM",
            "reason": "GOOGLE_API_KEY is missing; using fallback triage.",
            "response_text": "I could not run full triage right now. If symptoms are severe, seek urgent care.",
        }

    prompt = (
        "You are a medical triage assistant. "
        "Classify the severity into: LOW, MEDIUM, HIGH, CRITICAL based on the user message and history. "
        "You MUST return valid JSON exactly in this format: "
        "{\"severity\":\"...\",\"reason\":\"...\",\"response_text\":\"A calm, brief response to the user\"}.\n\n"
        f"Recent conversation history:\n{history or 'No prior history.'}\n\n"
        f"Latest user message:\n{user_message}"
    )

    model = genai.GenerativeModel("gemini-2.5-flash")
    response = await model.generate_content_async(prompt)
    text = getattr(response, "text", "") or ""

    try:
        parsed = _extract_json_block(text)
    except Exception:
        parsed = {
            "severity": "MEDIUM",
            "reason": "Model response could not be parsed as JSON.",
            "response_text": "I recommend getting checked by a healthcare professional soon.",
        }

    severity = str(parsed.get("severity", "MEDIUM")).upper()
    if severity not in {"LOW", "MEDIUM", "HIGH", "CRITICAL"}:
        severity = "MEDIUM"

    return {
        "severity": severity,
        "reason": str(parsed.get("reason", "No reason provided.")),
        "response_text": str(parsed.get("response_text", "Please seek medical care if symptoms worsen.")),
    }


async def get_nearby_hospitals(lat: float, lng: float) -> list[dict[str, Any]]:
    if not GOOGLE_API_KEY:
        return []

    params = {
        "location": f"{lat},{lng}",
        "radius": 5000,
        "type": "hospital",
        "key": GOOGLE_API_KEY,
    }
    url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            payload = response.json()
    except httpx.HTTPError:
        return []

    hospitals: list[dict[str, Any]] = []
    for item in payload.get("results", [])[:3]:
        geo = item.get("geometry", {}).get("location", {})
        hospitals.append(
            {
                "name": item.get("name", "Unknown Hospital"),
                "address": item.get("vicinity", item.get("formatted_address", "Address unavailable")),
                "location": {
                    "lat": geo.get("lat"),
                    "lng": geo.get("lng"),
                },
            }
        )

    return hospitals


async def stream_mock_orchestrator(
    session_id: str,
    user_message: str,
    history: list[dict[str, str]],
    history_str: str,
    latitude: float | None = None,
    longitude: float | None = None,
) -> AsyncGenerator[dict[str, Any], None]:
    _ = (session_id, history)

    yield {
        "status": "processing",
        "agent": "Triage Agent",
        "message": "Analyzing symptoms...",
    }

    triage = await run_triage(user_message=user_message, history=history_str)
    severity = triage.get("severity", "MEDIUM")
    reason = triage.get("reason", "No reason provided.")
    response_text = triage.get("response_text", "Please seek medical care if symptoms worsen.")

    yield {
        "status": "processing",
        "agent": "Maps Agent",
        "message": "Checking location for nearby facilities...",
    }

    hospital_list: list[dict[str, Any]] = []
    if severity in ["HIGH", "CRITICAL"] and latitude is not None and longitude is not None:
        hospital_list = await get_nearby_hospitals(latitude, longitude)

    yield {
        "type": "final",
        "severity": severity,
        "reason": reason,
        "response": response_text,
        "hospitals": hospital_list,
    }


def run_analysis(request: AnalyzeRequest) -> AnalyzeResponse:
    language_output = process_language(request.text)
    triage = triage_symptoms(language_output.simplified_text)
    navigation = find_nearby_hospitals(triage.risk_level, request.location)
    emergency = emergency_response(triage.risk_level)
    summary = build_summary(
        original_text=request.text,
        location=request.location,
        language_output=language_output,
        triage=triage,
        navigation=navigation,
        emergency=emergency,
    )
    provider_message = format_provider_message(summary)

    return AnalyzeResponse(
        language_output=language_output,
        triage=triage,
        navigation=navigation,
        summary=summary,
        provider_message=provider_message.message,
        emergency_flag=emergency.emergency_flag,
        emergency=emergency,
    )


def run_communication(summary) -> CommunicationResponse:
    return format_provider_message(summary)
