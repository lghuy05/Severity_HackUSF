# Health Equity Bridge (Severity)

Health Equity Bridge is an AI-assisted healthcare navigation app designed to reduce access barriers for patients who face language, cost, and care-navigation challenges.

It combines a `Next.js` frontend, a `FastAPI` backend, and a local multi-agent orchestration layer that can:

- translate and normalize symptom descriptions
- assess urgency with deterministic safety overrides
- recommend nearby care options
- estimate likely care costs
- generate provider-facing summaries
- support multilingual, stateful chat flows

## Demo

[![Watch the video](https://img.youtube.com/vi/qeR0itcqT6U/maxresdefault.jpg)](https://youtu.be/qeR0itcqT6U)

### [Severity](https://youtu.be/qeR0itcqT6U)

## Why This Project Exists

Many patients do not fail because care is unavailable. They fail because the path to care is confusing.

This project focuses on practical barriers:

- language mismatch between patients and providers
- uncertainty about urgency
- difficulty finding appropriate nearby care
- lack of cost transparency
- poor handoff quality when moving from chat to real care

## What’s Implemented

### Core user flow

- Conversational symptom intake with session state
- Structured follow-up questions when information is missing
- Triage with hybrid AI + deterministic emergency rules
- Care navigation using Google Places
- Cost estimation with fallback heuristics
- Provider-facing summary generation
- Streaming chat responses to the frontend

### Extended workflows

- Visit note extraction from transcripts
- Conversation summarization
- Turn-by-turn translation
- Appointment workflow hooks, including VAPI-based scheduling integration
- User profile persistence via Firebase or local file fallback

## Architecture

This is an **agent-oriented monolith**, not a distributed system.

Authoritative runtime path:

`frontend -> backend/main.py -> backend/orchestrator.py -> a2a/router.py -> specialized/* -> tools/*`

### High-level execution flow

1. The frontend sends a symptom or chat request.
2. The backend creates a typed `AgentMessage` state object.
3. The orchestrator extracts semantic meaning and determines the next action.
4. Specialized agents handle language, triage, emergency guidance, navigation, cost, and provider handoff.
5. Tool adapters call Gemini, Google Places, Firebase, and scheduling services.
6. The backend returns structured outputs, session state, and trace data for UI visualization.

### Specialized agents

- `language_agent`: language detection, simplification, translation
- `triage_agent`: urgency assessment with deterministic overrides
- `emergency_agent`: urgent guidance for high-risk symptom patterns
- `navigation_agent`: nearby care search
- `cost_agent`: care cost estimation
- `contact_agent`: provider handoff summary generation

## Why It’s Technically Interesting

- Uses **typed orchestration** instead of free-form prompt chaining
- Combines **LLM reasoning with deterministic safety logic**
- Maintains **multi-turn conversation state** with follow-up resolution
- Streams responses and exposes **traceable agent execution** to the UI
- Includes fallback behavior when external AI or API dependencies fail

## Tech Stack

### Frontend

- Next.js App Router
- TypeScript
- Tailwind CSS

### Backend

- FastAPI
- Pydantic
- Firebase / Firestore fallback storage

### AI and orchestration

- Gemini
- Modular local multi-agent orchestration
- Local A2A-style agent handoff router

### External integrations

- Google Places API
- VAPI

## Repository Structure

```text
frontend/        Next.js UI
backend/         FastAPI routes, orchestration entrypoints, persistence helpers
specialized/     Specialized agent implementations
tools/           Gemini, maps, cost, formatting, profile helpers
a2a/             Local A2A-style handoff router
core/            Base agent runtime, tracing, response assembly
shared/          Shared schemas and TS/Python type bridge
tests/           Orchestration and tool tests
docs/            Architecture notes and demo script
```

