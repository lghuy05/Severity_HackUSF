# Architecture

## Overview

Health Equity Bridge is a lightweight monorepo with three core layers:

1. `frontend/`: Next.js UI for chat, voice input, hospital map, and agent visualization
2. `backend/`: FastAPI API layer
3. `agents/`: Google ADK + A2A-style modular agents

## Agent Pipeline

1. Voice/text input enters the frontend.
2. The backend remains an API boundary and can call the agent package when needed.
3. Inside `agents/`, `root_agent` delegates to `language_agent` to normalize the message.
4. `triage_agent` assigns low, medium, or high risk.
5. `emergency_agent` is triggered for high-risk cases.
6. `navigation_agent` returns nearby hospitals with mock coordinates.
7. `summary_agent` builds a structured payload.
8. `communication_agent` formats a provider-ready handoff message.

## Design Notes

- The backend and agent runtime are intentionally separated so teammates can work independently.
- Each specialized agent is instantiated as an ADK-backed unit configured for Gemini.
- A lightweight A2A router logs explicit agent-to-agent delegation for hackathon demos and judging.
- Shared schemas keep the API predictable across frontend and backend.
- The frontend animates agent progress to make multi-agent reasoning visible during a live demo.
