# Architecture

## Overview

Health Equity Bridge is a lightweight monorepo with three core layers:

1. `frontend/`: Next.js UI for chat, voice input, hospital map, and agent visualization
2. `backend/`: FastAPI API with a simple orchestrator
3. `agents/`: Modular A2A-style function-based agents

## Agent Pipeline

1. Voice/text input enters the frontend.
2. `language_agent` normalizes the message and detects language.
3. `triage_agent` assigns low, medium, or high risk using simple rules.
4. `navigation_agent` returns nearby hospitals with mock coordinates.
5. `emergency_agent` adds urgent instructions when risk is high.
6. `summary_agent` builds a structured payload.
7. `communication_agent` formats a provider-ready handoff message.

## Design Notes

- The orchestrator is intentionally simple and demoable.
- Agents are isolated Python modules so they can later be replaced with Google ADK or external services.
- Shared schemas keep the API predictable across frontend and backend.
- The frontend animates agent progress to make multi-agent reasoning visible during a live demo.
