# Severity

Health Equity Bridge is a local multi-agent healthcare navigator built with:

- `frontend/`: Next.js App Router UI
- `backend/`: FastAPI API surface
- `specialized/`: specialized healthcare agents
- `tools/`: Gemini, Google Places, and formatter integrations
- `a2a/`: local A2A-style handoff router
- `core/`: shared agent runtime, tracing, and response assembly
- `shared/`: TypeScript and Python schema bridge

## Authoritative Runtime

The authoritative runtime path is:

`frontend -> backend/main.py -> backend/orchestrator.py -> a2a/router.py -> specialized/* -> tools/*`

The `agents/` package is retained as a compatibility surface and ADK configuration layer. It is no longer the primary place where orchestration logic lives.

## Run

### Backend

```bash
cd /home/yui/Work/hackathon/Severity/backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd /home/yui/Work/hackathon/Severity
backend/.venv/bin/python -m uvicorn backend.main:app --reload --port 8000
```

Required environment:

```env
GEMINI_API_KEY=...
GOOGLE_MAPS_API_KEY=...
```

Optional:

```env
GEMINI_MODEL=gemini-2.5-flash
GEMINI_TEMPERATURE=0.2
```

### Frontend

```bash
cd /home/yui/Work/hackathon/Severity/frontend
npm install
npm run dev
```

Set:

```env
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

### Direct Root-Agent Smoke Test

```bash
cd /home/yui/Work/hackathon/Severity
agents/.venv/bin/python test_rootagent.py
```

## Current Flow

1. Frontend submits text plus location to `POST /analyze`.
2. FastAPI validates the request and calls the orchestrator.
3. The orchestrator delegates through:
   `language_agent -> triage_agent -> emergency_agent? -> navigation_agent -> cost_agent -> contact_agent`
4. Agents enrich a shared `AgentMessage` state object.
5. Backend returns structured outputs plus a request trace for frontend visualization.
