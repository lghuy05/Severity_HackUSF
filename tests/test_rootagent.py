from __future__ import annotations

import json
import os
import sys
from pathlib import Path

try:
    from dotenv import load_dotenv
except ModuleNotFoundError:  # pragma: no cover
    load_dotenv = None


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from backend.orchestrator import orchestrator
from backend.schemas import AnalyzeRequest


def bootstrap_env() -> None:
    if load_dotenv is None:
        return

    for name in (".env", ".env.local"):
        env_path = ROOT / name
        if env_path.exists():
            load_dotenv(env_path, override=False)


def main() -> None:
    bootstrap_env()

    text = os.getenv("ROOT_AGENT_TEST_TEXT", "I have chest pain and shortness of breath")
    location = os.getenv("ROOT_AGENT_TEST_LOCATION", "Tampa, Florida")

    response = orchestrator.run_pipeline(
        AnalyzeRequest(
            text=text,
            location=location,
        )
    )

    print("Root agent test completed")
    print(f"request_id: {response.request_id}")
    print(f"risk_level: {response.triage.risk_level}")
    print(f"emergency_flag: {response.emergency_flag}")
    print(f"hospitals_found: {len(response.navigation.hospitals)}")
    print(f"cost_options_found: {len(response.cost_options)}")
    print(f"use_adk_runtime: {os.getenv('USE_ADK_RUNTIME', '0')}")
    print()
    print(json.dumps(response.model_dump(mode="json"), indent=2))


if __name__ == "__main__":
    main()
