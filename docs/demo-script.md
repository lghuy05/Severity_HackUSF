# Demo Script

1. Open the frontend and explain that the product accepts free-form symptom input.
2. Submit a high-risk prompt such as `I have chest pain and shortness of breath`.
3. Point out the staged agent flow: language, triage, navigation, cost, action.
4. Show that the backend returns emergency guidance plus nearby real facilities from Google Places.
5. Highlight the estimated cost options and provider-facing summary in the returned response.
6. If needed, run `agents/.venv/bin/python test_rootagent.py` to show the full structured trace.
7. Close by explaining that the system uses a single orchestrator, explicit A2A handoffs, specialized agents, and tool-backed integrations.
