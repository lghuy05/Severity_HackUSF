from shared.schemas import TriageOutput


HIGH_RISK_KEYWORDS = {
    "chest pain",
    "shortness of breath",
    "trouble breathing",
    "stroke",
    "fainted",
    "severe bleeding",
    "dizzy",
    "unconscious",
}

MEDIUM_RISK_KEYWORDS = {
    "fever",
    "infection",
    "vomiting",
    "asthma",
    "dehydrated",
    "migraine",
}


def triage_symptoms(symptoms_text: str) -> TriageOutput:
    normalized = symptoms_text.lower()

    if any(keyword in normalized for keyword in HIGH_RISK_KEYWORDS):
        return TriageOutput(
            risk_level="high",
            explanation="Symptoms indicate a potentially urgent condition that should be evaluated immediately.",
        )

    if any(keyword in normalized for keyword in MEDIUM_RISK_KEYWORDS):
        return TriageOutput(
            risk_level="medium",
            explanation="Symptoms suggest prompt medical follow-up, but they do not appear immediately life-threatening.",
        )

    return TriageOutput(
        risk_level="low",
        explanation="Symptoms appear lower risk based on simple rules and should be monitored with routine follow-up.",
    )
