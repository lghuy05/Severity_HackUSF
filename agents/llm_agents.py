"""
Pricing Agent -- uses Gemini to estimate out-of-pocket treatment costs.
Language Agent -- uses Gemini to simplify and translate medical text.
"""

import json
import os
import re

import google.generativeai as genai

MODEL_NAME = "gemini-2.0-flash"


def _extract_json(text: str) -> dict:
    """Robustly extract a JSON object from Gemini's response."""
    cleaned = re.sub(r"```(?:json)?\s*", "", text)
    cleaned = cleaned.strip().rstrip("`")
    match = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        return {
            "estimated_cost_range": "Unable to estimate",
            "reasoning": text[:300],
        }


async def estimate_costs(diagnosis: str) -> dict:
    """
    Use Gemini to estimate average out-of-pocket costs in the US
    for the given diagnosis/reason.

    Returns
    -------
    dict  with keys: estimated_cost_range, reasoning
    """
    api_key = os.getenv("GOOGLE_API_KEY", "")
    if not api_key:
        return {
            "estimated_cost_range": "N/A",
            "reasoning": "API key not configured.",
        }

    genai.configure(api_key=api_key)

    prompt = (
        f"Diagnosis / reason for visit: {diagnosis}\n\n"
        "Estimate the average out-of-pocket cost in the US for this medical issue. "
        "Consider both insured and uninsured scenarios. "
        "Return ONLY valid JSON with exactly these keys:\n"
        '{"estimated_cost_range": "$X - $Y", "reasoning": "..."}'
    )

    try:
        model = genai.GenerativeModel(model_name=MODEL_NAME)
        response = await model.generate_content_async(prompt)
        return _extract_json(response.text)
    except Exception as exc:
        return {
            "estimated_cost_range": "Unable to estimate",
            "reasoning": f"Gemini error: {exc}",
        }


async def simplify_and_translate(medical_text: str, target_language: str = "en") -> str:
    """
    Use Gemini to simplify medical text for a non-technical reader,
    then translate it into the target language.

    Returns
    -------
    str  -- the simplified, translated text
    """
    api_key = os.getenv("GOOGLE_API_KEY", "")
    if not api_key:
        return medical_text  # passthrough if no key

    genai.configure(api_key=api_key)

    prompt = (
        "You are a medical communicator. "
        "Simplify the following medical text so a non-technical person "
        "can understand it perfectly. "
        f"Then, translate it into {target_language}. "
        "Return ONLY the simplified, translated text -- no JSON, no extra commentary.\n\n"
        f"Medical text:\n{medical_text}"
    )

    try:
        model = genai.GenerativeModel(model_name=MODEL_NAME)
        response = await model.generate_content_async(prompt)
        return response.text.strip()
    except Exception as exc:
        print(f"[WARN] Language agent error: {exc}")
        return medical_text  # fallback to original
