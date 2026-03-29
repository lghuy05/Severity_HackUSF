from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class ModelConfig:
    model_name: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    api_key: str = os.getenv("GEMINI_API_KEY", "")
    temperature: float = float(os.getenv("GEMINI_TEMPERATURE", "0.2"))


MODEL_CONFIG = ModelConfig()


def get_gemini_model():
    try:
        from google.adk.models.google_llm import Gemini
    except ModuleNotFoundError:
        return None

    return Gemini(model=MODEL_CONFIG.model_name)
