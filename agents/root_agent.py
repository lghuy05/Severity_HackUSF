from backend.orchestrator import orchestrator
from backend.schemas import AnalyzeRequest, AnalyzeResponse


root_agent = orchestrator


def run_pipeline(user_input: str, location: str = "Unknown location") -> AnalyzeResponse:
    return orchestrator.run_pipeline(AnalyzeRequest(text=user_input, location=location))
