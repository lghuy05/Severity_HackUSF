# Agents

Google ADK + A2A-style multi-agent package for the healthcare navigator.

## Scope

This folder is intentionally separate from `backend/`.

- `agents/` owns agent definitions, routing, and Gemini/ADK setup.
- `backend/` owns FastAPI endpoints and API orchestration.

## Setup

```bash
cd agents
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Set:

```env
GEMINI_API_KEY=your_key
```

Optional:

```env
GEMINI_MODEL=gemini-2.5-flash
```

## Layout

- `core/base_agent.py`: ADK-backed agent wrapper
- `core/agent_registry.py`: shared agent registry
- `core/a2a_router.py`: visible A2A-style message routing
- `language_agent.py`: translation and simplification
- `triage_agent.py`: low/medium/high risk classification
- `navigation_agent.py`: mock care-site recommendations
- `summary_agent.py`: structured JSON summary
- `communication_agent.py`: provider handoff formatting
- `emergency_agent.py`: urgent escalation guidance
- `root_agent.py`: orchestrator and `run_pipeline(...)`

## Quick Test

```bash
cd /home/yui/Work/hackathon/Severity
PYTHONPATH=. agents/.venv/bin/python - <<'PY'
from agents.root_agent import run_pipeline

result = run_pipeline("I feel chest pain and dizzy", "San Francisco, CA")
print(result.model_dump())
PY
```
