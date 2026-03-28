# Severity

Demo-ready MVP for an AI multi-agent healthcare navigator with a Next.js frontend and FastAPI backend.

## Structure

- `frontend/`: Next.js App Router UI with chat, voice input, map, and agent flow panel
- `backend/`: FastAPI API and orchestrator
- `agents/`: Google ADK-style multi-agent package with A2A routing
- `shared/`: Shared schemas and TypeScript types
- `docs/`: Architecture notes and demo script

## Run

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

Set `GEMINI_API_KEY=your_key` before starting the backend.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Set `NEXT_PUBLIC_API_BASE_URL=http://localhost:8000` in `frontend/.env.local`.

Optional:

- Set `NEXT_PUBLIC_GOOGLE_MAPS_API_KEY` to render the Google Map script instead of the placeholder map panel.

## Demo Flow

1. Enter or dictate a symptom like `I feel chest pain and dizzy`.
2. Frontend sends `/analyze` request with text and location.
3. Backend orchestrator runs the ADK root agent, which routes A2A-style messages across language, triage, navigation, emergency, summary, and communication agents.
4. UI updates the agent flow panel in real time.
5. Emergency mode appears automatically for high-risk cases.
