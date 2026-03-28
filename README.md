# Severity

Demo-ready MVP for an AI multi-agent healthcare navigator with a Next.js frontend, a FastAPI backend, and a separate Google ADK agent package.

## Structure

- `frontend/`: Next.js App Router UI with chat, voice input, map, and agent flow panel
- `backend/`: FastAPI API layer
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

### Agents

```bash
cd agents
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Set `GEMINI_API_KEY=your_key` before running the ADK agents.

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
3. The backend can call into the agent package, but the FastAPI app and ADK agent runtime are set up independently.
4. UI updates the agent flow panel in real time.
5. Emergency mode appears automatically for high-risk cases.
