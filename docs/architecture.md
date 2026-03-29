# Architecture

## Overview

Health Equity Bridge currently runs as a single local application with these layers:

1. `frontend/`: Next.js UI for symptom input, progressive guidance, map, cost, and emergency actions
2. `backend/`: FastAPI request boundary and orchestration entrypoint
3. `specialized/`: specialized agent implementations
4. `tools/`: external integrations and non-LLM logic
5. `a2a/`: local A2A-style handoff router
6. `core/`: tracing, base runtime, and response assembly

## Authoritative Execution Path

1. Frontend submits `POST /analyze`.
2. `backend/main.py` validates input and calls `backend/orchestrator.py`.
3. The orchestrator creates a single `AgentMessage` state object.
4. The A2A router performs explicit handoffs between specialized agents.
5. Agents call tools for Gemini and Google Places integration.
6. The final response is assembled into API-safe output and returned with a trace.

## Agent Pipeline

1. `language_agent`: normalize and translate the user message
2. `triage_agent`: assess urgency
3. `emergency_agent`: inject urgent instructions for high-risk cases
4. `navigation_agent`: find nearby care sites via Google Places
5. `cost_agent`: generate structured care-cost estimates
6. `contact_agent`: prepare a provider-facing handoff summary

## Notes

- `agents/` now acts primarily as compatibility exports plus ADK configuration helpers.
- The old `summary_agent` concept has been absorbed into response assembly and provider handoff generation.
- A2A is explicit and traceable, but local to the process rather than distributed.
- ADK objects are instantiated, but the current runtime still executes through local orchestrator and agent methods.
