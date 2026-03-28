"""
Live Triage Agent -- uses Google Gemini to classify symptom severity.

Returns a structured dict:
    {
        "severity": "LOW" | "MEDIUM" | "HIGH" | "CRITICAL",
        "reason": "...",
        "response_text": "A calm, brief response to the user"
    }
"""

import json
import os
import re

import google.generativeai as genai

MODEL_NAME = "gemini-2.0-flash"

SYSTEM_PROMPT = """\
You are a medical triage assistant for a health equity application.

Your job is to evaluate the user's message (and recent conversation history)
and classify the situation into one of four severity levels:
  LOW      -- minor issue, self-care advice is appropriate
  MEDIUM   -- should see a doctor soon, but not an emergency
  HIGH     -- needs urgent care or ER visit today
  CRITICAL -- life-threatening, call 911 immediately

You MUST return valid JSON only -- no markdown fences, no extra text.
Use exactly this schema:
{
  "severity": "LOW | MEDIUM | HIGH | CRITICAL",
  "reason": "A one-sentence clinical justification",
  "response_text": "A calm, empathetic, 1-3 sentence response to the user"
}
"""


def _extract_json(text: str) -> dict:
    """
    Robustly extract a JSON object from Gemini's response.
    Handles markdown code fences, leading prose, etc.
    """
    # Strip markdown code fences
    cleaned = re.sub(r"```(?:json)?\s*", "", text)
    cleaned = cleaned.strip().rstrip("`")

    # Find the first { ... } block
    match = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    # Fallback: try the whole cleaned string
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        return {
            "severity": "MEDIUM",
            "reason": "Unable to parse LLM response -- defaulting to MEDIUM.",
            "response_text": text[:300],
        }


async def run_triage(user_message: str, history: str) -> dict:
    """
    Call Gemini to classify the severity of the user's symptoms.

    Parameters
    ----------
    user_message : str
        The latest message from the user.
    history : str
        A compact string of recent conversation context.

    Returns
    -------
    dict  with keys: severity, reason, response_text
    """
    api_key = os.getenv("GOOGLE_API_KEY", "")
    if not api_key:
        return {
            "severity": "MEDIUM",
            "reason": "GOOGLE_API_KEY not set -- returning mock severity.",
            "response_text": "I'm unable to reach the AI service right now. Please try again.",
        }

    genai.configure(api_key=api_key)

    prompt = (
        f"Conversation history:\n{history}\n\n"
        f"Latest user message:\n{user_message}\n\n"
        "Classify this and respond with valid JSON."
    )

    try:
        model = genai.GenerativeModel(
            model_name=MODEL_NAME,
            system_instruction=SYSTEM_PROMPT,
        )
        response = await model.generate_content_async(prompt)
        raw = response.text
        return _extract_json(raw)

    except Exception as exc:
        return {
            "severity": "MEDIUM",
            "reason": f"Gemini call failed: {exc}",
            "response_text": "I encountered an issue processing your symptoms. Please describe them again.",
        }
