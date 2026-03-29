from __future__ import annotations

from backend.schemas import AgentMessage
from backend.schemas import AgentFlowStep, AnalyzeResponse, EmergencyOutput, LanguageOutput, NavigationOutput, SummaryOutput, TriageOutput


FLOW_DEFINITIONS = [
    ("language_agent", "Language"),
    ("triage_agent", "Triage"),
    ("emergency_agent", "Emergency"),
    ("navigation_agent", "Navigation"),
    ("cost_agent", "Cost"),
    ("contact_agent", "Contact"),
]


def build_agent_flow(message: AgentMessage) -> list[AgentFlowStep]:
    started_agents = {event.agent for event in message.trace if event.event == "agent_started" and event.agent}
    completed_agents = {event.agent for event in message.trace if event.event == "agent_completed" and event.agent}
    tools_by_agent: dict[str, list[str]] = {}
    for event in message.trace:
        if event.tool and event.agent:
            tools_by_agent.setdefault(event.agent, [])
            if event.tool not in tools_by_agent[event.agent]:
                tools_by_agent[event.agent].append(event.tool)

    summaries = {
        "language_agent": message.translated_text or message.normalized_text or message.raw_text,
        "triage_agent": f"{message.risk_level or 'unknown'} risk",
        "emergency_agent": "Urgent guidance prepared" if message.emergency_flag else "No emergency escalation",
        "navigation_agent": f"{len(message.hospitals)} care options found",
        "cost_agent": f"{len(message.cost_options)} cost estimates prepared",
        "contact_agent": message.provider_summary or "Provider handoff prepared",
    }

    flow: list[AgentFlowStep] = []
    for agent, label in FLOW_DEFINITIONS:
        if agent in completed_agents:
            status = "done"
        elif agent in started_agents:
            status = "running"
        else:
            status = "pending"
        flow.append(
            AgentFlowStep(
                agent=agent,
                label=label,
                status=status,
                summary=summaries.get(agent, ""),
                tools=tools_by_agent.get(agent, []),
            )
        )
    return flow


def build_response(message: AgentMessage) -> AnalyzeResponse:
    return AnalyzeResponse(
        request_id=message.request_id,
        language_output=LanguageOutput(
            detected_language=message.detected_language or "en",
            simplified_text=message.normalized_text or message.raw_text,
            translated_text=message.translated_text or message.normalized_text or message.raw_text,
        ),
        triage=TriageOutput(
            risk_level=message.risk_level or "low",
            explanation=message.risk_reason or "",
        ),
        navigation=NavigationOutput(
            origin=message.location,
            recommendation=(
                "Head to the nearest emergency department now."
                if message.risk_level == "high"
                else "Here are nearby care options based on your location."
            ),
            hospitals=message.hospitals,
        ),
        summary=SummaryOutput(
            patient_input=message.raw_text,
            location=message.location,
            detected_language=message.detected_language or "en",
            normalized_text=message.translated_text or message.normalized_text or message.raw_text,
            risk_level=message.risk_level or "low",
            triage_explanation=message.risk_reason or "",
            recommended_sites=[hospital.name for hospital in message.hospitals],
            emergency_flag=message.emergency_flag,
            emergency_instructions=message.emergency_instructions,
        ),
        provider_message=message.provider_summary or "",
        emergency_flag=message.emergency_flag,
        emergency=EmergencyOutput(
            emergency_flag=message.emergency_flag,
            instructions=message.emergency_instructions,
        ),
        cost_options=message.cost_options,
        agent_flow=build_agent_flow(message),
        trace=message.trace,
    )
