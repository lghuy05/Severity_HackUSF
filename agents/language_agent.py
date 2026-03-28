from shared.schemas import LanguageOutput


SPANISH_HINTS = {"dolor", "mareado", "pecho", "ayuda", "hospital"}


def process_language(raw_text: str) -> LanguageOutput:
    lowered = raw_text.lower()
    detected_language = "es" if any(token in lowered for token in SPANISH_HINTS) else "en"
    simplified_text = " ".join(raw_text.strip().split())

    if detected_language == "es":
        translated_text = "I have pain and need medical help."
    else:
        translated_text = simplified_text

    return LanguageOutput(
        detected_language=detected_language,
        simplified_text=simplified_text,
        translated_text=translated_text,
    )
