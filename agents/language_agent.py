from agents.core.base_agent import create_agent
from shared.schemas import LanguageOutput


SPANISH_HINTS = {"dolor", "mareado", "pecho", "ayuda", "hospital"}


def process_language(raw_text: str) -> LanguageOutput:
    lowered = raw_text.lower()
    detected_language = "es" if any(token in lowered for token in SPANISH_HINTS) else "en"
    simplified_text = " ".join(raw_text.strip().split())
    translated_text = "I have pain and need medical help." if detected_language == "es" else simplified_text

    return LanguageOutput(
        detected_language=detected_language,
        simplified_text=simplified_text,
        translated_text=translated_text,
    )


language_agent = create_agent(
    key="language",
    name="language_agent",
    instruction=(
        "Translate input into clear, simple English. "
        "Return a normalized version that downstream healthcare agents can use."
    ),
    handler=lambda message, _context: process_language(str(message)),
    metadata={"role": "translation_and_simplification"},
)
