# Agents

This folder is now a compatibility and ADK-support surface, not the sole source of truth for orchestration.

## What Is Authoritative

The authoritative runtime is:

- `backend/orchestrator.py`
- `specialized/`
- `tools/`
- `a2a/router.py`
- `core/`

The files in `agents/` primarily provide:

- ADK model/config helpers
- compatibility exports for older imports
- a stable `agents.root_agent.run_pipeline(...)` convenience entrypoint

## Current Layout

- `config.py`: Gemini / ADK model configuration
- `message_types.py`: A2A envelope type
- `registry.py`: agent registry abstraction
- `root_agent.py`: compatibility wrapper around the backend orchestrator
- `language_agent.py`, `triage_agent.py`, `navigation_agent.py`, `communication_agent.py`, `emergency_agent.py`: compatibility exports that point to the specialized agents

## Quick Test

```bash
cd /home/yui/Work/hackathon/Severity
agents/.venv/bin/python test_rootagent.py
```

## Important Note

The current codebase instantiates ADK agent objects, but orchestration still happens through the local Python orchestrator and A2A router. Future ADK-runtime work should build on the specialized agents rather than reintroducing a second execution path here.
