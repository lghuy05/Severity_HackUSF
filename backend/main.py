from pathlib import Path
import sys

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from backend.orchestrator import run_analysis, run_communication
from shared.schemas import AnalyzeRequest, AnalyzeResponse, CommunicationRequest, CommunicationResponse

app = FastAPI(title="Health Equity Bridge API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/analyze", response_model=AnalyzeResponse)
def analyze(request: AnalyzeRequest):
    return run_analysis(request)


@app.post("/communicate", response_model=CommunicationResponse)
def communicate(request: CommunicationRequest):
    return run_communication(request.summary)
