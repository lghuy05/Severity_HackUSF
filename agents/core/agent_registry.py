from agents.communication_agent import communication_agent
from agents.emergency_agent import emergency_agent
from agents.language_agent import language_agent
from agents.navigation_agent import navigation_agent
from agents.summary_agent import summary_agent
from agents.triage_agent import triage_agent


AGENTS = {
    "language": language_agent,
    "triage": triage_agent,
    "navigation": navigation_agent,
    "summary": summary_agent,
    "communication": communication_agent,
    "emergency": emergency_agent,
}


def get_agent(agent_key: str):
    try:
        return AGENTS[agent_key]
    except KeyError as exc:
        raise ValueError(f"Unknown agent '{agent_key}'. Registered agents: {sorted(AGENTS)}") from exc
