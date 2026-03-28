import json
import os
import re
from typing import Any

import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)


def _extract_json_block(text: str) -> dict[str, Any]:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\\s*", "", cleaned)
        cleaned = re.sub(r"\\s*```$", "", cleaned)

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
        "{\"severity\":\"...\",\"reason\":\"...\",\"response_text\":\"A calm, brief response to the user\"}.\\n\\n"
        f"Recent conversation history:\\n{history or 'No prior history.'}\\n\\n"
        f"Latest user message:\\n{user_message}"
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


async def estimate_costs(diagnosis: str) -> dict[str, str]:
    if not GOOGLE_API_KEY:
        return {
            "estimated_cost_range": "$200 - $1200",
            "reasoning": "GOOGLE_API_KEY is missing; using fallback estimate.",
        }

    prompt = (
        "Estimate average out-of-pocket medical costs in the US for this diagnosis context: "
        f"{diagnosis}. "
        "Return valid JSON only in this format: "
        "{\"estimated_cost_range\":\"$X - $Y\",\"reasoning\":\"...\"}."
    )

    model = genai.GenerativeModel("gemini-2.5-flash")
    response = await model.generate_content_async(prompt)
    text = getattr(response, "text", "") or ""

    try:
        parsed = _extract_json_block(text)
    except Exception:
        parsed = {
            "estimated_cost_range": "$300 - $1500",
            "reasoning": "Model response was not valid JSON, fallback estimate used.",
        }

    return {
        "estimated_cost_range": str(parsed.get("estimated_cost_range", "$300 - $1500")),
        "reasoning": str(parsed.get("reasoning", "Estimated using typical urgent care and diagnostics costs.")),
    }


async def simplify_and_translate(medical_text: str, target_language: str) -> str:
    if not GOOGLE_API_KEY:
        return medical_text

    prompt = (
        "You are a medical communicator. Simplify the following medical text so a non-technical person "
        f"can understand it perfectly. Then, translate it into {target_language}. "
        "Return ONLY the simplified, translated text.\\n\\n"
        f"Medical text:\\n{medical_text}"
    )

    model = genai.GenerativeModel("gemini-2.5-flash")
    response = await model.generate_content_async(prompt)
    text = (getattr(response, "text", "") or "").strip()
    return text or medical_text


async def generate_summary_report(history: str) -> dict[str, Any]:
    if not GOOGLE_API_KEY:
        return {
            "patient_complaint": "Not available",
            "triage_severity": "MEDIUM",
            "recommended_actions": ["Seek clinical review if symptoms worsen."],
            "extracted_symptoms": [],
        }

    prompt = (
        "Generate a structured JSON medical report based on this triage conversation. "
        "Required JSON keys: patient_complaint, triage_severity, recommended_actions, extracted_symptoms.\\n\\n"
        f"Conversation:\\n{history}"
    )

    model = genai.GenerativeModel("gemini-2.5-flash")
    response = await model.generate_content_async(prompt)
    text = getattr(response, "text", "") or ""

    try:
        parsed = _extract_json_block(text)
    except Exception:
        parsed = {
            "patient_complaint": "Unable to parse report",
            "triage_severity": "MEDIUM",
            "recommended_actions": ["Review full transcript manually."],
            "extracted_symptoms": [],
        }

    if not isinstance(parsed.get("recommended_actions"), list):
        parsed["recommended_actions"] = [str(parsed.get("recommended_actions", ""))]
    if not isinstance(parsed.get("extracted_symptoms"), list):
        parsed["extracted_symptoms"] = [str(parsed.get("extracted_symptoms", ""))]

    return parsed
