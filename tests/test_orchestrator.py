import unittest
from importlib.util import find_spec
import os
from pathlib import Path
from unittest.mock import patch

from backend.orchestrator import orchestrator
from backend.schemas import AnalyzeRequest, ChatTurnRequest, SemanticMeaning

try:
    from dotenv import load_dotenv
except ModuleNotFoundError:  # pragma: no cover
    load_dotenv = None


ROOT = Path(__file__).resolve().parents[1]


def bootstrap_env() -> None:
    if load_dotenv is None:
        return
    for name in (".env", ".env.local"):
        path = ROOT / name
        if path.exists():
            load_dotenv(path, override=False)


class OrchestratorTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        bootstrap_env()

    def test_high_risk_pipeline_routes_to_emergency_and_navigation(self) -> None:
        response = orchestrator.run_pipeline(
            AnalyzeRequest(text="I feel chest pain and dizzy", location="San Francisco, CA")
        )

        self.assertEqual(response.triage.risk_level, "high")
        self.assertTrue(response.emergency_flag)
        self.assertTrue(response.emergency.instructions)
        self.assertTrue(response.cost_options)
        self.assertTrue(response.trace)

        events = [event.event for event in response.trace]
        agents = [event.agent for event in response.trace if event.agent]

        self.assertIn("request_received", events)
        self.assertIn("handoff_to_agent", events)
        self.assertIn("tool_called", events)
        self.assertIn("pipeline_completed", events)
        self.assertIn("emergency_agent", agents)
        self.assertIn("navigation_agent", agents)

        if os.getenv("GOOGLE_MAPS_API_KEY") and os.getenv("LIVE_EXTERNAL_TESTS") == "1":
            self.assertTrue(
                response.navigation.hospitals,
                "Expected live Google Places results when GOOGLE_MAPS_API_KEY is configured.",
            )
        else:
            self.assertIsInstance(response.navigation.hospitals, list)

    def test_natural_language_navigation_routes_without_button_click(self) -> None:
        def semantic_by_message(*args, **kwargs):
            latest_message = kwargs.get("message") if "message" in kwargs else args[0]
            if latest_message == "I have a headache":
                return SemanticMeaning(
                    intent="symptom_check",
                    symptoms=["headache"],
                    severity="unknown",
                    urgency="low",
                    user_goal="get_advice",
                    has_enough_info=False,
                    follow_up_needed=True,
                    follow_up_question="How strong is the pain right now?",
                    follow_up_kind="multiple_choice",
                    follow_up_options=["Mild", "Moderate", "Severe"],
                    is_new_case=True,
                )
            if latest_message == "Moderate":
                return SemanticMeaning(
                    intent="symptom_check",
                    symptoms=["headache"],
                    severity="moderate",
                    urgency="medium",
                    user_goal="get_advice",
                    has_enough_info=True,
                    follow_up_needed=False,
                    follow_up_question=None,
                    follow_up_kind="free_text",
                    follow_up_options=[],
                    is_new_case=False,
                )
            return SemanticMeaning(
                intent="seek_care",
                symptoms=[],
                severity="moderate",
                urgency="medium",
                user_goal="find_hospital",
                has_enough_info=True,
                follow_up_needed=False,
                follow_up_question=None,
                follow_up_kind="free_text",
                follow_up_options=[],
                is_new_case=False,
            )

        with patch("backend.orchestrator.extract_structured_meaning", side_effect=semantic_by_message):
            symptom_turn = orchestrator.run_chat_turn(
                ChatTurnRequest(intent="symptoms", message="I have a headache", location="Tampa, Florida")
            )

            session_id = symptom_turn.session_id
            follow_up_turn = orchestrator.run_chat_turn(
                ChatTurnRequest(
                    session_id=session_id,
                    intent="symptoms",
                    message="Moderate",
                    location="Tampa, Florida",
                )
            )

            care_turn = orchestrator.run_chat_turn(
                ChatTurnRequest(
                    session_id=session_id,
                    intent="symptoms",
                    message="Can you find a hospital near me?",
                    location="Tampa, Florida",
                )
        )

        self.assertEqual(follow_up_turn.state.stage, "decision")
        self.assertEqual(care_turn.state.stage, "navigation")
        self.assertIn("looked for care near you", care_turn.assistant_message.lower())
        navigation_agents = [event.agent for event in care_turn.trace if event.agent]
        self.assertIn("navigation_agent", navigation_agents)
        self.assertIsNone(care_turn.response.follow_up)

    def test_natural_language_guidance_routes_without_button_click(self) -> None:
        meanings = iter(
            [
                SemanticMeaning(
                    intent="symptom_check",
                    symptoms=["fever"],
                    severity="unknown",
                    urgency="medium",
                    user_goal="get_advice",
                    has_enough_info=True,
                    follow_up_needed=False,
                    follow_up_question=None,
                    follow_up_kind="free_text",
                    follow_up_options=[],
                    is_new_case=True,
                ),
                SemanticMeaning(
                    intent="guidance",
                    symptoms=[],
                    severity="unknown",
                    urgency="medium",
                    user_goal="get_advice",
                    has_enough_info=True,
                    follow_up_needed=False,
                    follow_up_question=None,
                    follow_up_kind="free_text",
                    follow_up_options=[],
                    is_new_case=False,
                ),
            ]
        )

        with patch("backend.orchestrator.extract_structured_meaning", side_effect=lambda *args, **kwargs: next(meanings)):
            session_id = orchestrator.run_chat_turn(
                ChatTurnRequest(intent="symptoms", message="I have a fever", location="Tampa, Florida")
            ).session_id

            turn = orchestrator.run_chat_turn(
                ChatTurnRequest(
                    session_id=session_id,
                    intent="symptoms",
                    message="What should I do?",
                    location="Tampa, Florida",
                )
            )

        self.assertEqual(turn.state.stage, "decision")
        self.assertIn("next step", turn.assistant_message.lower())

    def test_natural_language_triage_reassesses_severity(self) -> None:
        meanings = iter(
            [
                SemanticMeaning(
                    intent="symptom_check",
                    symptoms=["chest pain"],
                    severity="unknown",
                    urgency="medium",
                    user_goal="get_advice",
                    has_enough_info=True,
                    follow_up_needed=False,
                    follow_up_question=None,
                    follow_up_kind="free_text",
                    follow_up_options=[],
                    is_new_case=True,
                ),
                SemanticMeaning(
                    intent="emergency",
                    symptoms=["chest pain"],
                    severity="severe",
                    urgency="high",
                    user_goal="get_advice",
                    has_enough_info=True,
                    follow_up_needed=False,
                    follow_up_question=None,
                    follow_up_kind="free_text",
                    follow_up_options=[],
                    is_new_case=False,
                ),
            ]
        )

        with patch("backend.orchestrator.extract_structured_meaning", side_effect=lambda *args, **kwargs: next(meanings)):
            session_id = orchestrator.run_chat_turn(
                ChatTurnRequest(intent="symptoms", message="I have chest pain", location="Tampa, Florida")
            ).session_id

            turn = orchestrator.run_chat_turn(
                ChatTurnRequest(
                    session_id=session_id,
                    intent="symptoms",
                    message="It is getting worse and feels severe now",
                    location="Tampa, Florida",
                )
            )

        self.assertEqual(turn.state.stage, "decision")
        self.assertEqual(turn.state.risk, "high")
        self.assertTrue(turn.session.emergency_flag)

    def test_headache_asks_severity_follow_up(self) -> None:
        meaning = SemanticMeaning(
            intent="symptom_check",
            symptoms=["headache"],
            severity="unknown",
            urgency="low",
            user_goal="get_advice",
            has_enough_info=False,
            follow_up_needed=True,
            follow_up_question="How strong is the headache right now?",
            follow_up_kind="multiple_choice",
            follow_up_options=["Mild", "Moderate", "Severe"],
            is_new_case=True,
        )

        with patch("backend.orchestrator.extract_structured_meaning", return_value=meaning):
            turn = orchestrator.run_chat_turn(
                ChatTurnRequest(intent="symptoms", message="I have a headache", location="Tampa, Florida")
            )

        self.assertEqual(turn.state.stage, "clarify")
        self.assertIsNotNone(turn.response.follow_up)
        assert turn.response.follow_up is not None
        self.assertEqual(turn.response.follow_up.text, "How strong is the headache right now?")

    def test_follow_up_answer_five_of_ten_resolves_severity_without_reasking(self) -> None:
        meanings = iter(
            [
                SemanticMeaning(
                    intent="symptom_check",
                    symptoms=["headache"],
                    severity="unknown",
                    urgency="low",
                    user_goal="get_advice",
                    has_enough_info=False,
                    follow_up_needed=True,
                    follow_up_question="How strong is the headache right now?",
                    follow_up_kind="multiple_choice",
                    follow_up_options=["Mild", "Moderate", "Severe"],
                    is_new_case=True,
                ),
                SemanticMeaning(
                    intent="symptom_check",
                    symptoms=["headache"],
                    severity="moderate",
                    urgency="medium",
                    user_goal="get_advice",
                    has_enough_info=True,
                    follow_up_needed=False,
                    follow_up_question=None,
                    follow_up_kind="free_text",
                    follow_up_options=[],
                    is_new_case=False,
                ),
            ]
        )

        with patch("backend.orchestrator.extract_structured_meaning", side_effect=lambda *args, **kwargs: next(meanings)):
            first = orchestrator.run_chat_turn(
                ChatTurnRequest(intent="symptoms", message="I have a headache", location="Tampa, Florida")
            )
            second = orchestrator.run_chat_turn(
                ChatTurnRequest(
                    session_id=first.session_id,
                    intent="symptoms",
                    message="It's about 5/10",
                    location="Tampa, Florida",
                )
            )

        self.assertEqual(second.state.severity, "moderate")
        self.assertIsNone(second.response.follow_up)
        self.assertEqual(second.session.follow_up_answers.get("semantic_follow_up"), "It's about 5/10")

    def test_follow_up_fallback_maps_numeric_scale_when_semantic_output_is_still_unknown(self) -> None:
        meanings = iter(
            [
                SemanticMeaning(
                    intent="symptom_check",
                    symptoms=["headache"],
                    severity="unknown",
                    urgency="low",
                    user_goal="get_advice",
                    has_enough_info=False,
                    follow_up_needed=True,
                    follow_up_question="How strong is the headache right now?",
                    follow_up_kind="multiple_choice",
                    follow_up_options=["Mild", "Moderate", "Severe"],
                    is_new_case=True,
                ),
                SemanticMeaning(
                    intent="symptom_check",
                    symptoms=["headache"],
                    severity="unknown",
                    urgency="low",
                    user_goal="get_advice",
                    has_enough_info=False,
                    follow_up_needed=True,
                    follow_up_question="How strong is the headache right now?",
                    follow_up_kind="multiple_choice",
                    follow_up_options=["Mild", "Moderate", "Severe"],
                    is_new_case=False,
                ),
            ]
        )

        with patch("backend.orchestrator.extract_structured_meaning", side_effect=lambda *args, **kwargs: next(meanings)):
            first = orchestrator.run_chat_turn(
                ChatTurnRequest(intent="symptoms", message="I have a headache", location="Tampa, Florida")
            )
            second = orchestrator.run_chat_turn(
                ChatTurnRequest(
                    session_id=first.session_id,
                    intent="symptoms",
                    message="5/10",
                    location="Tampa, Florida",
                )
            )

        self.assertEqual(second.state.severity, "moderate")
        self.assertIsNone(second.response.follow_up)

    def test_pending_follow_up_resolves_plain_numeric_answer_with_semantic_first(self) -> None:
        meanings = iter(
            [
                SemanticMeaning(
                    intent="symptom_check",
                    symptoms=["headache"],
                    severity="unknown",
                    urgency="low",
                    user_goal="get_advice",
                    has_enough_info=False,
                    follow_up_needed=True,
                    follow_up_question="How strong is the headache right now?",
                    follow_up_kind="multiple_choice",
                    follow_up_options=["Mild", "Moderate", "Severe"],
                    is_new_case=True,
                ),
                SemanticMeaning(
                    intent="symptom_check",
                    symptoms=["headache"],
                    severity="unknown",
                    urgency="low",
                    user_goal="get_advice",
                    has_enough_info=False,
                    follow_up_needed=True,
                    follow_up_question="How strong is the headache right now?",
                    follow_up_kind="multiple_choice",
                    follow_up_options=["Mild", "Moderate", "Severe"],
                    is_new_case=False,
                ),
            ]
        )

        with patch("backend.orchestrator.extract_structured_meaning", side_effect=lambda *args, **kwargs: next(meanings)) as mock_semantic:
            first = orchestrator.run_chat_turn(
                ChatTurnRequest(intent="symptoms", message="I have a headache", location="Tampa, Florida")
            )
            second = orchestrator.run_chat_turn(
                ChatTurnRequest(
                    session_id=first.session_id,
                    intent="symptoms",
                    message="3",
                    location="Tampa, Florida",
                )
            )

        self.assertEqual(second.state.severity, "mild")
        self.assertIsNone(second.response.follow_up)
        self.assertEqual(mock_semantic.call_count, 2)

    def test_follow_up_fallback_maps_vague_severity_language(self) -> None:
        meanings = iter(
            [
                SemanticMeaning(
                    intent="symptom_check",
                    symptoms=["headache"],
                    severity="unknown",
                    urgency="low",
                    user_goal="get_advice",
                    has_enough_info=False,
                    follow_up_needed=True,
                    follow_up_question="How strong is the headache right now?",
                    follow_up_kind="multiple_choice",
                    follow_up_options=["Mild", "Moderate", "Severe"],
                    is_new_case=True,
                ),
                SemanticMeaning(
                    intent="symptom_check",
                    symptoms=["headache"],
                    severity="unknown",
                    urgency="low",
                    user_goal="get_advice",
                    has_enough_info=False,
                    follow_up_needed=True,
                    follow_up_question="How strong is the headache right now?",
                    follow_up_kind="multiple_choice",
                    follow_up_options=["Mild", "Moderate", "Severe"],
                    is_new_case=False,
                ),
            ]
        )

        with patch("backend.orchestrator.extract_structured_meaning", side_effect=lambda *args, **kwargs: next(meanings)):
            first = orchestrator.run_chat_turn(
                ChatTurnRequest(intent="symptoms", message="I have a headache", location="Tampa, Florida")
            )
            second = orchestrator.run_chat_turn(
                ChatTurnRequest(
                    session_id=first.session_id,
                    intent="symptoms",
                    message="It's kinda bad",
                    location="Tampa, Florida",
                )
            )

        self.assertEqual(second.state.severity, "moderate")
        self.assertIsNone(second.response.follow_up)

    def test_cost_routes_immediately_from_natural_language(self) -> None:
        meanings = iter(
            [
                SemanticMeaning(
                    intent="symptom_check",
                    symptoms=["headache"],
                    severity="moderate",
                    urgency="medium",
                    user_goal="get_advice",
                    has_enough_info=True,
                    follow_up_needed=False,
                    follow_up_question=None,
                    follow_up_kind="free_text",
                    follow_up_options=[],
                    is_new_case=True,
                ),
                SemanticMeaning(
                    intent="cost",
                    symptoms=[],
                    severity="moderate",
                    urgency="medium",
                    user_goal="compare_cost",
                    has_enough_info=True,
                    follow_up_needed=False,
                    follow_up_question=None,
                    follow_up_kind="free_text",
                    follow_up_options=[],
                    is_new_case=False,
                ),
            ]
        )

        with patch("backend.orchestrator.extract_structured_meaning", side_effect=lambda *args, **kwargs: next(meanings)):
            first = orchestrator.run_chat_turn(
                ChatTurnRequest(intent="symptoms", message="I have a headache", location="Tampa, Florida")
            )
            second = orchestrator.run_chat_turn(
                ChatTurnRequest(
                    session_id=first.session_id,
                    intent="symptoms",
                    message="How much would it cost?",
                    location="Tampa, Florida",
                )
        )

        self.assertEqual(second.state.stage, "cost")
        self.assertIn("costs", second.response.ui_blocks)

    def test_one_user_message_produces_one_assistant_message_chunk(self) -> None:
        meaning = SemanticMeaning(
            intent="symptom_check",
            symptoms=["headache"],
            severity="moderate",
            urgency="medium",
            user_goal="get_advice",
            has_enough_info=True,
            follow_up_needed=False,
            follow_up_question=None,
            follow_up_kind="free_text",
            follow_up_options=[],
            is_new_case=True,
        )

        with patch("backend.orchestrator.extract_structured_meaning", return_value=meaning):
            chunks = orchestrator.stream_chat_turn(
                ChatTurnRequest(intent="symptoms", message="I have a headache", location="Tampa, Florida")
            )

        message_chunks = [chunk for chunk in chunks if chunk.type == "message"]
        self.assertEqual(len(message_chunks), 1)
        self.assertEqual(message_chunks[0].message, chunks[-1].response.message)

    @unittest.skipUnless(find_spec("httpx") is not None, "httpx is required for FastAPI TestClient")
    def test_analyze_endpoint_returns_structured_trace(self) -> None:
        from fastapi.testclient import TestClient

        from backend.main import app

        client = TestClient(app)

        response = client.post(
            "/analyze",
            json={"text": "I feel chest pain and dizzy", "location": "San Francisco, CA"},
        )

        self.assertEqual(response.status_code, 200)

        payload = response.json()
        self.assertEqual(payload["triage"]["risk_level"], "high")
        self.assertTrue(payload["emergency_flag"])
        self.assertTrue(payload["navigation"]["hospitals"])
        self.assertTrue(payload["trace"])
        self.assertEqual(payload["trace"][-1]["event"], "pipeline_completed")


if __name__ == "__main__":
    unittest.main()
