from shared.schemas import EmergencyOutput


def emergency_response(risk_level: str) -> EmergencyOutput:
    if risk_level == "high":
        return EmergencyOutput(
            emergency_flag=True,
            instructions=[
                "Call 911 immediately if symptoms are severe or worsening.",
                "Do not drive yourself if you feel faint, confused, or short of breath.",
                "Go to the nearest emergency department now.",
            ],
        )

    return EmergencyOutput(
        emergency_flag=False,
        instructions=["No emergency escalation required based on current triage rules."],
    )
