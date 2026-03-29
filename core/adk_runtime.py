from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass
from typing import Any
from uuid import uuid4

from agents.config import get_gemini_model


logger = logging.getLogger(__name__)


@dataclass(slots=True)
class ADKRunResult:
    text: str
    raw_events: list[dict]


class ADKRuntimeError(RuntimeError):
    pass


def run_adk_structured_agent(
    *,
    agent_name: str,
    instruction: str,
    prompt: str,
    response_schema: dict,
) -> ADKRunResult:
    try:
        from google.adk.agents.llm_agent import Agent as ADKAgent
        from google.adk.runners import InMemoryRunner
        from google.genai import types
    except ModuleNotFoundError as exc:  # pragma: no cover - depends on env
        raise ADKRuntimeError("google-adk is not installed in the current environment") from exc

    model = get_gemini_model()
    if model is None:
        raise ADKRuntimeError("Gemini model is not available for ADK execution")

    agent = ADKAgent(
        name=agent_name,
        model=model,
        instruction=instruction,
        tools=[],
        output_schema=response_schema,
        generate_content_config=types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=0.2,
        ),
    )

    async def _invoke() -> ADKRunResult:
        runner = InMemoryRunner(agent=agent, app_name=f"{agent_name}_runtime")
        user_id = "health_equity_bridge"
        session_id = str(uuid4())
        await runner.session_service.create_session(
            app_name=runner.app_name,
            user_id=user_id,
            session_id=session_id,
        )

        raw_events: list[dict] = []
        final_text = ""

        try:
            async for event in runner.run_async(
                user_id=user_id,
                session_id=session_id,
                new_message=types.Content(
                    role="user",
                    parts=[types.Part(text=prompt)],
                ),
            ):
                raw_events.append(
                    {
                        "author": event.author,
                        "is_final": event.is_final_response(),
                        "has_content": bool(event.content and event.content.parts),
                    }
                )
                if event.author == agent_name and event.content and event.content.parts:
                    text_chunks = [part.text for part in event.content.parts if part.text]
                    if text_chunks:
                        final_text = "".join(text_chunks)
        finally:
            await runner.close()

        if not final_text:
            raise ADKRuntimeError(f"ADK agent {agent_name} returned no final text")

        return ADKRunResult(text=final_text, raw_events=raw_events)

    return asyncio.run(_invoke())


def parse_adk_json_output(result: ADKRunResult) -> dict:
    try:
        return json.loads(result.text)
    except json.JSONDecodeError as exc:
        raise ADKRuntimeError(f"ADK output was not valid JSON: {result.text}") from exc
