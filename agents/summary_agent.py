from shared.schemas import EmergencyOutput, LanguageOutput, NavigationOutput, SummaryOutput, TriageOutput


def build_summary(
    original_text: str,
    location: str,
    language_output: LanguageOutput,
    triage: TriageOutput,
    navigation: NavigationOutput,
    emergency: EmergencyOutput,
) -> SummaryOutput:
    return SummaryOutput(
        patient_input=original_text,
        location=location,
        detected_language=language_output.detected_language,
        normalized_text=language_output.translated_text,
        risk_level=triage.risk_level,
        triage_explanation=triage.explanation,
        recommended_sites=[hospital.name for hospital in navigation.hospitals],
        emergency_flag=emergency.emergency_flag,
        emergency_instructions=emergency.instructions,
    )
