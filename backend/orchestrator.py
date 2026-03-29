from __future__ import annotations

import logging
import re

from agents.registry import AgentRegistry
from a2a.router import A2ARouter
from backend.schemas import (
    AssistantState,
    AssistantTurnPayload,
    AgentMessage,
    AnalyzeRequest,
    AnalyzeResponse,
    ChatStreamChunk,
    FollowUpQuestion,
    ChatTurnRequest,
    ChatTurnResponse,
    ChatSessionState,
    CommunicationResponse,
    QuickAction,
    SummaryOutput,
    SemanticMeaning,
    UserProfile,
)
from core.runner import build_agent_flow, build_response
from core.tracing import append_trace, trace_span
from backend.session_store import session_store
from specialized.contact_agent import ContactAgent
from specialized.cost_agent import CostAgent
from specialized.emergency_agent import EmergencyAgent
from specialized.language_agent import LanguageAgent
from specialized.navigation_agent import NavigationAgent
from specialized.triage_agent import TriageAgent
from tools.gemini_tool import GeminiToolError, extract_structured_meaning, generate_assistant_reply, translate_text_items
from tools.message_formatter import format_provider_message


logger = logging.getLogger(__name__)


class HealthcareOrchestrator:
    def __init__(self, *, use_adk: bool = False) -> None:
        self.use_adk = use_adk
        self.registry = AgentRegistry(
            [
                LanguageAgent(),
                TriageAgent(),
                NavigationAgent(),
                CostAgent(),
                ContactAgent(),
                EmergencyAgent(),
            ]
        )
        self.router = A2ARouter(self.registry)

    def _should_trigger_emergency(
        self,
        *,
        raw_text: str,
        normalized_text: str | None = None,
        detected_symptoms: list[str] | None = None,
        known_symptom: str | None = None,
    ) -> bool:
        text = " ".join(
            part.strip().lower()
            for part in [raw_text, normalized_text or "", known_symptom or ""]
            if part and part.strip()
        )
        symptoms = {item.strip().lower() for item in (detected_symptoms or []) if item.strip()}

        emergency_phrases = {
            "chest pain",
            "shortness of breath",
            "trouble breathing",
            "difficulty breathing",
            "breathing difficulty",
            "stroke",
            "fainted",
            "fainting",
            "severe bleeding",
            "unconscious",
            "seizure",
            "passed out",
        }
        emergency_combinations = [
            {"chest pain", "dizzy"},
            {"chest pain", "dizziness"},
            {"chest pain", "shortness of breath"},
            {"chest pain", "trouble breathing"},
        ]

        if any(phrase in text for phrase in emergency_phrases):
            return True
        if any(group.issubset(symptoms) for group in emergency_combinations):
            return True
        if "call 911" in text or "ambulance" in text:
            return True
        return False

    def _session_to_message(self, request: ChatTurnRequest) -> AgentMessage:
        session = request.session or (session_store.get(request.session_id) if request.session_id else None)
        profile = request.profile or (session.profile if session else UserProfile(location=request.location))
        raw_text = (request.message or (session.raw_text if session else "") or "").strip()
        payload: dict[str, object] = {
            "user_id": request.user_id or (session.user_id if session else None),
            "location": request.location,
            "raw_text": raw_text,
            "preferred_language": request.preferred_language or profile.language or (session.preferred_language if session else None),
            "normalized_text": session.normalized_text if session else None,
            "detected_language": session.detected_language if session else None,
            "translated_text": session.translated_text if session else None,
            "risk_level": session.risk_level if session else None,
            "risk_reason": session.risk_reason if session else None,
            "hospitals": list(session.hospitals) if session else [],
            "cost_options": list(session.cost_options) if session else [],
            "provider_summary": session.provider_summary if session else None,
            "emergency_flag": session.emergency_flag if session else False,
            "emergency_instructions": list(session.emergency_instructions) if session else [],
            "metadata": {
                "use_adk": self.use_adk,
                "consent_to_fetch_external": bool(session.consent_to_fetch_external) if session else False,
                "profile": profile.model_dump(mode="json"),
                "conversation_summary": session.conversation_summary if session else "",
                "messages": session.messages if session else [],
                "follow_up_answers": session.follow_up_answers if session else {},
                "pending_question": session.pending_question.model_dump(mode="json") if session and session.pending_question else None,
                "assistant_state": session.state.model_dump(mode="json") if session else AssistantState().model_dump(mode="json"),
            },
        }
        if session and session.request_id:
            payload["request_id"] = session.request_id
        return AgentMessage(**payload)

    def _message_to_session(self, message: AgentMessage) -> ChatSessionState:
        return ChatSessionState(
            session_id=message.request_id,
            request_id=message.request_id,
            user_id=message.user_id,
            location=message.location,
            preferred_language=message.preferred_language,
            raw_text=message.raw_text,
            normalized_text=message.normalized_text,
            detected_language=message.detected_language,
            translated_text=message.translated_text,
            risk_level=message.risk_level,
            risk_reason=message.risk_reason,
            hospitals=message.hospitals,
            cost_options=message.cost_options,
            provider_summary=message.provider_summary,
            emergency_flag=message.emergency_flag,
            emergency_instructions=message.emergency_instructions,
            consent_to_fetch_external=bool(message.metadata.get("consent_to_fetch_external", False)),
            profile=UserProfile(**message.metadata.get("profile", {})),
            state=AssistantState(**message.metadata.get("assistant_state", {})),
            pending_question=message.metadata.get("pending_question"),
            follow_up_answers=message.metadata.get("follow_up_answers", {}),
            messages=message.metadata.get("messages", []),
            conversation_summary=str(message.metadata.get("conversation_summary", "")),
        )

    def _get_state(self, message: AgentMessage) -> AssistantState:
        return AssistantState(**message.metadata.get("assistant_state", {}))

    def _set_state(self, message: AgentMessage, state: AssistantState) -> None:
        message.metadata["assistant_state"] = state.model_dump(mode="json")

    def _history_items(self, message: AgentMessage) -> list[dict[str, str]]:
        history: list[dict[str, str]] = []
        for item in list(message.metadata.get("messages", [])):
            if isinstance(item, dict):
                history.append(
                    {
                        "role": str(item.get("role", "assistant")),
                        "content": str(item.get("content", "")),
                    }
                )
            else:
                history.append(
                    {
                        "role": str(getattr(item, "role", "assistant")),
                        "content": str(getattr(item, "content", "")),
                    }
                )
        return history

    def _summarize_older_turns(self, history: list[dict[str, str]], *, keep_recent: int = 3) -> str:
        older_turns = history[:-keep_recent] if len(history) > keep_recent else []
        if not older_turns:
            return ""

        condensed: list[str] = []
        for item in older_turns[-4:]:
            content = " ".join(item["content"].split())
            if not content:
                continue
            condensed.append(f"{item['role']}: {content[:70]}")
        return " | ".join(condensed)

    def _recent_turns(self, message: AgentMessage, *, limit: int = 3) -> list[dict[str, str]]:
        history = self._history_items(message)
        recent = history[-limit:]
        return [
            {"role": item["role"], "content": " ".join(item["content"].split())[:160]}
            for item in recent
            if item["content"].strip()
        ]

    def _refresh_conversation_memory(self, message: AgentMessage) -> None:
        history = self._history_items(message)
        message.metadata["messages"] = history
        message.metadata["conversation_summary"] = self._summarize_older_turns(history)

    def _profile_context(self, message: AgentMessage) -> dict[str, object]:
        profile = message.metadata.get("profile", {})
        if isinstance(profile, dict):
            return profile
        return {}

    def _extract_semantic_meaning(
        self,
        message: AgentMessage,
        state: AssistantState,
        pending_question: FollowUpQuestion | None = None,
    ) -> SemanticMeaning:
        try:
            meaning = extract_structured_meaning(
                message=message.raw_text,
                state=state,
                conversation_summary=str(message.metadata.get("conversation_summary", "")),
                pending_question=pending_question,
                follow_up_answers=message.metadata.get("follow_up_answers", {}),
                recent_turns=self._recent_turns(message),
                profile=self._profile_context(message),
            )
            append_trace(
                message,
                event="tool_called",
                agent="root_agent",
                tool="semantic_understanding",
                detail=f"Semantic intent={meaning.intent}, urgency={meaning.urgency}",
            )
            return meaning
        except GeminiToolError:
            append_trace(
                message,
                event="tool_called",
                agent="root_agent",
                tool="semantic_understanding_fallback",
                detail="Semantic extraction fell back to conservative defaults.",
            )
            return SemanticMeaning(
                intent="unclear",
                symptoms=[state.symptom] if state.symptom else [],
                severity=state.severity if state.severity in {"mild", "moderate", "severe"} else "unknown",
                urgency=state.risk if state.risk in {"low", "medium", "high"} else "low",
                user_goal="unclear",
                has_enough_info=bool(state.symptom),
                follow_up_needed=not bool(state.symptom),
                follow_up_field=None if state.symptom else "symptom",
                follow_up_question=None if state.symptom else "Can you tell me the main symptom you are feeling?",
                follow_up_kind="free_text",
                follow_up_options=[],
                is_new_case=False,
            )

    def _reset_case_state(self, message: AgentMessage) -> AssistantState:
        message.normalized_text = None
        message.translated_text = None
        message.detected_language = None
        message.risk_level = None
        message.risk_reason = None
        message.hospitals = []
        message.cost_options = []
        message.provider_summary = None
        message.emergency_flag = False
        message.emergency_instructions = []
        message.metadata["pending_question"] = None
        message.metadata["follow_up_answers"] = {}
        return AssistantState(stage="intake")

    def _merge_symptoms(self, existing: str | None, incoming: list[str], replace: bool) -> str | None:
        cleaned = [item.strip() for item in incoming if isinstance(item, str) and item.strip()]
        if not cleaned:
            return existing
        if replace or not existing:
            return ", ".join(dict.fromkeys(cleaned))
        merged = [part.strip() for part in existing.split(",") if part.strip()]
        merged.extend(cleaned)
        return ", ".join(dict.fromkeys(merged))

    def is_field_missing(self, state: AssistantState, field: str | None) -> bool:
        if not field or field == "other":
            return True
        value = getattr(state, field, None)
        return value in [None, "", "unknown"]

    def _merge_state_from_meaning(self, state: AssistantState, meaning: SemanticMeaning) -> AssistantState:
        merged = state.model_copy(deep=True)
        merged.symptom = self._merge_symptoms(state.symptom, meaning.symptoms, replace=meaning.is_new_case)
        if meaning.severity != "unknown":
            merged.severity = meaning.severity
        if meaning.resolved_field == "severity" and meaning.resolved_value in {"mild", "moderate", "severe"}:
            merged.severity = meaning.resolved_value
        if meaning.urgency in {"low", "medium", "high"}:
            merged.risk = meaning.urgency

        if meaning.intent == "seek_care":
            merged.intent = "care"
            merged.stage = "navigation"
        elif meaning.intent == "cost":
            merged.intent = "cost"
            merged.stage = "cost"
        elif meaning.intent == "guidance":
            merged.intent = "guidance"
            merged.stage = "decision"
        elif meaning.intent == "emergency":
            merged.intent = "guidance"
            merged.stage = "triage"
            merged.risk = "high"
        else:
            merged.intent = "symptoms"
            if meaning.follow_up_needed and meaning.urgency != "high":
                merged.stage = "clarify"
            elif meaning.urgency == "high":
                merged.stage = "triage"
            elif merged.symptom:
                merged.stage = "decision"
            else:
                merged.stage = "intake"

        merged.missing_fields = ["follow_up"] if meaning.follow_up_needed and meaning.urgency != "high" else []
        return merged

    def _infer_follow_up_field(
        self,
        *,
        meaning: SemanticMeaning,
        pending_question: FollowUpQuestion | None,
    ) -> str | None:
        if meaning.follow_up_field:
            return meaning.follow_up_field
        if pending_question and meaning.answered_pending_question:
            return None
        return None

    def _suppress_follow_up(self, meaning: SemanticMeaning) -> SemanticMeaning:
        adjusted = meaning.model_copy(deep=True)
        adjusted.follow_up_needed = False
        adjusted.follow_up_field = None
        adjusted.follow_up_question = None
        adjusted.follow_up_kind = "free_text"
        adjusted.follow_up_options = []
        return adjusted

    def _reconcile_follow_up_with_known_state(
        self,
        *,
        state: AssistantState,
        meaning: SemanticMeaning,
        pending_question: FollowUpQuestion | None,
        message: AgentMessage,
    ) -> SemanticMeaning:
        adjusted = meaning.model_copy(deep=True)
        if (
            pending_question
            and adjusted.answered_pending_question
            and adjusted.follow_up_needed
            and adjusted.follow_up_question
            and adjusted.follow_up_question.strip().lower() == pending_question.text.strip().lower()
        ):
            adjusted = self._suppress_follow_up(adjusted)
            append_trace(
                message,
                event="state_updated",
                agent="root_agent",
                detail="Cleared repeated follow-up because the pending question was already answered this turn.",
            )
        return adjusted

    def _validate_semantic_follow_up(
        self,
        *,
        state_before: AssistantState,
        merged_state: AssistantState,
        meaning: SemanticMeaning,
        pending_question: FollowUpQuestion | None,
        message: AgentMessage,
    ) -> SemanticMeaning:
        if not meaning.follow_up_needed or not meaning.follow_up_question:
            return meaning

        adjusted = meaning.model_copy(deep=True)
        adjusted.follow_up_field = self._infer_follow_up_field(meaning=adjusted, pending_question=pending_question)
        target_field = adjusted.follow_up_field

        if target_field and not self.is_field_missing(merged_state, target_field):
            append_trace(
                message,
                event="state_updated",
                agent="root_agent",
                detail=f"Suppressed semantic follow-up for known field '{target_field}'.",
            )
            return self._suppress_follow_up(adjusted)

        if pending_question and adjusted.answered_pending_question and adjusted.follow_up_needed:
            if not target_field:
                append_trace(
                    message,
                    event="state_updated",
                    agent="root_agent",
                    detail="Suppressed ambiguous semantic follow-up after resolving the pending question.",
                )
                return self._suppress_follow_up(adjusted)
            if target_field == pending_question.expected_field:
                append_trace(
                    message,
                    event="state_updated",
                    agent="root_agent",
                    detail=f"Suppressed repeated follow-up for already resolved field '{target_field}'.",
                )
                return self._suppress_follow_up(adjusted)
            if target_field in {"symptom", "severity"} and (
                not self.is_field_missing(state_before, target_field) or not self.is_field_missing(merged_state, target_field)
            ):
                append_trace(
                    message,
                    event="state_updated",
                    agent="root_agent",
                    detail=f"Suppressed contradictory follow-up after resolution because '{target_field}' is already known.",
                )
                return self._suppress_follow_up(adjusted)

        return adjusted

    def _record_follow_up_answer(
        self,
        message: AgentMessage,
        pending_question: FollowUpQuestion | None,
        user_text: str,
        answered: bool,
    ) -> None:
        if pending_question is None or not user_text.strip():
            return
        answers = dict(message.metadata.get("follow_up_answers", {}))
        if answered:
            answers[pending_question.question_id] = user_text.strip()
        message.metadata["follow_up_answers"] = answers

    def _parse_severity_answer(self, user_text: str) -> str | None:
        text = user_text.strip().lower()
        if not text:
            return None

        direct_number = re.fullmatch(r"\s*(10|[1-9])\s*", text)
        if direct_number:
            value = int(direct_number.group(1))
            if value <= 3:
                return "mild"
            if value <= 6:
                return "moderate"
            return "severe"

        scale_match = re.search(r"\b(10|[1-9])\s*/\s*10\b", text)
        if scale_match:
            value = int(scale_match.group(1))
            if value <= 3:
                return "mild"
            if value <= 6:
                return "moderate"
            return "severe"

        if any(phrase in text for phrase in ["not too bad", "a little", "slight", "minor"]):
            return "mild"
        if any(phrase in text for phrase in ["kinda bad", "kind of bad", "pretty bad", "somewhat bad", "moderate"]):
            return "moderate"
        if any(phrase in text for phrase in ["very bad", "really bad", "much worse", "severe", "unbearable", "extreme"]):
            return "severe"
        return None

    def _parse_yes_no_answer(self, user_text: str) -> str | None:
        text = user_text.strip().lower()
        if text in {"yes", "y", "yeah", "yep", "true"}:
            return "yes"
        if text in {"no", "n", "nope", "false"}:
            return "no"
        return None

    def _try_resolve_followup_answer(
        self,
        *,
        pending_question: FollowUpQuestion | None,
        user_text: str,
        state: AssistantState,
        message: AgentMessage,
    ) -> tuple[bool, AssistantState]:
        if pending_question is None or not user_text.strip():
            return False, state

        updated_state = state.model_copy(deep=True)

        if pending_question.expected_field == "severity":
            parsed = self._parse_severity_answer(user_text)
            if parsed:
                updated_state.severity = parsed
                if updated_state.risk not in {"high", "medium"}:
                    if parsed == "severe":
                        updated_state.risk = "high"
                    elif parsed == "moderate":
                        updated_state.risk = "medium"
                    else:
                        updated_state.risk = updated_state.risk or "low"
                updated_state.stage = "decision"
                updated_state.missing_fields = []
                append_trace(
                    message,
                    event="state_updated",
                    agent="root_agent",
                    detail=f"Resolved pending severity follow-up deterministically as {parsed}.",
                )
                return True, updated_state

        if pending_question.expected_field == "breathing":
            parsed = self._parse_yes_no_answer(user_text)
            if parsed == "yes":
                updated_state.risk = "high"
                updated_state.stage = "decision"
                updated_state.missing_fields = []
                append_trace(
                    message,
                    event="state_updated",
                    agent="root_agent",
                    detail="Resolved breathing follow-up deterministically as yes.",
                )
                return True, updated_state
            if parsed == "no":
                updated_state.stage = "decision"
                updated_state.missing_fields = []
                append_trace(
                    message,
                    event="state_updated",
                    agent="root_agent",
                    detail="Resolved breathing follow-up deterministically as no.",
                )
                return True, updated_state

        return False, state

    def _apply_follow_up_fallback(
        self,
        *,
        pending_question: FollowUpQuestion | None,
        user_text: str,
        state: AssistantState,
        meaning: SemanticMeaning,
        message: AgentMessage,
    ) -> tuple[AssistantState, SemanticMeaning, bool]:
        if pending_question is None or not user_text.strip():
            return state, meaning, False

        updated_state = state.model_copy(deep=True)
        updated_meaning = meaning.model_copy(deep=True)
        answered = False

        if pending_question.expected_field == "severity":
            parsed = self._parse_severity_answer(user_text)
            if parsed:
                updated_state.severity = parsed
                updated_meaning.severity = parsed
                updated_meaning.answered_pending_question = True
                updated_meaning.resolved_field = "severity"
                updated_meaning.resolved_value = parsed
                updated_meaning.follow_up_needed = False
                updated_meaning.follow_up_field = None
                updated_meaning.follow_up_question = None
                updated_meaning.follow_up_options = []
                updated_meaning.has_enough_info = True
                answered = True
                append_trace(
                    message,
                    event="state_updated",
                    agent="root_agent",
                    detail=f"Severity resolved from follow-up fallback parser as {parsed}.",
                )
            elif updated_meaning.follow_up_needed and updated_meaning.follow_up_question == pending_question.text:
                updated_meaning.follow_up_field = "severity"
                updated_meaning.follow_up_question = "If you had to rate it from 1 to 10, how strong is it right now?"
                updated_meaning.follow_up_kind = "free_text"
                updated_meaning.follow_up_options = []

        return updated_state, updated_meaning, answered

    def _log_semantic_turn(
        self,
        *,
        message: AgentMessage,
        latest_user_message: str,
        pending_question: FollowUpQuestion | None,
        state_before: AssistantState,
        semantic_meaning: SemanticMeaning,
        state_after: AssistantState,
        chosen_action: str,
        response_payload: AssistantTurnPayload | None = None,
    ) -> None:
        logger.info(
            "semantic_turn",
            extra={
                "event_data": {
                    "event": "semantic_turn",
                    "request_id": message.request_id,
                    "latest_user_message": latest_user_message,
                    "pending_question_before": pending_question.model_dump(mode="json") if pending_question else None,
                    "semantic_meaning": semantic_meaning.model_dump(mode="json"),
                    "state_before": state_before.model_dump(mode="json"),
                    "state_after": state_after.model_dump(mode="json"),
                    "chosen_action": chosen_action,
                    "response_payload_summary": (
                        {
                            "message": response_payload.message[:180],
                            "follow_up": response_payload.follow_up.model_dump(mode="json") if response_payload and response_payload.follow_up else None,
                            "actions": [action.label for action in response_payload.actions] if response_payload else [],
                            "ui_blocks": response_payload.ui_blocks if response_payload else [],
                        }
                        if response_payload
                        else None
                    ),
                }
            },
        )

    def _build_follow_up_from_meaning(self, meaning: SemanticMeaning) -> FollowUpQuestion | None:
        if not meaning.follow_up_needed or not meaning.follow_up_question:
            return None
        expected_field = meaning.follow_up_field or "other"
        question_text = meaning.follow_up_question.lower()
        if expected_field == "other" and (meaning.severity == "unknown" or any(term in question_text for term in ["strong", "pain", "bad", "rate"])):
            expected_field = "severity"
        return FollowUpQuestion(
            question_id="semantic_follow_up",
            text=meaning.follow_up_question,
            kind=meaning.follow_up_kind,
            options=meaning.follow_up_options,
            expected_field=expected_field,
        )

    def _build_actions(self, state: AssistantState, meaning: SemanticMeaning, follow_up_question: FollowUpQuestion | None) -> list[QuickAction]:
        if follow_up_question is not None:
            return []
        actions: list[QuickAction] = []
        if state.risk == "high":
            actions.append(QuickAction(label="Find emergency care", intent="care", prompt="Find emergency care near me"))
            return actions
        if state.stage in {"decision", "triage"} or meaning.user_goal == "get_advice":
            actions.append(QuickAction(label="What should I do?", intent="guidance"))
            actions.append(QuickAction(label="Find care near me", intent="care"))
            actions.append(QuickAction(label="Compare cost", intent="cost"))
        elif state.stage == "navigation":
            actions.append(QuickAction(label="Compare cost", intent="cost"))
        return actions

    def _build_ui_blocks(self, message: AgentMessage, state: AssistantState) -> list[str]:
        blocks: list[str] = []
        if state.stage in {"decision", "triage"}:
            blocks.append("guidance")
        if message.emergency_flag:
            blocks.append("emergency")
        if message.hospitals:
            blocks.append("care_options")
        if message.cost_options:
            if "care_options" not in blocks:
                blocks.append("care_options")
            blocks.append("costs")
        return blocks

    def _generate_reply(
        self,
        *,
        message: AgentMessage,
        state: AssistantState,
        meaning: SemanticMeaning,
        follow_up_question: FollowUpQuestion | None,
    ) -> str:
        hospitals = [
            {
                "name": item.name,
                "address": item.address,
                "phone": item.phone,
            }
            for item in message.hospitals[:3]
        ]
        cost_options = [
            {
                "provider": item.provider,
                "estimated_cost": item.estimated_cost,
                "care_type": item.care_type,
            }
            for item in message.cost_options[:3]
        ]
        try:
            return generate_assistant_reply(
                latest_message=message.raw_text,
                state=state,
                meaning=meaning,
                risk_reason=message.risk_reason,
                hospitals=hospitals,
                cost_options=cost_options,
                emergency_instructions=message.emergency_instructions,
                follow_up_question=follow_up_question.text if follow_up_question else None,
                recent_turns=self._recent_turns(message),
                conversation_summary=str(message.metadata.get("conversation_summary", "")),
                profile=self._profile_context(message),
                target_language=(message.preferred_language or "en"),
            )
        except GeminiToolError:
            if follow_up_question:
                return f"I need one quick detail before I guide you further: {follow_up_question.text}"
            if state.stage == "navigation":
                return f"Got it. I looked for care near you and found {len(message.hospitals)} nearby options."
            if state.stage == "cost":
                return "I pulled together some rough cost guidance for the care options in front of you."
            if state.risk == "high":
                return "This could be urgent, so please get emergency care now."
            if state.risk == "medium":
                return "This is worth getting checked soon. I can help with the next step."
            return "This doesn't look urgent right now. I can help you decide what to do next."

    def _append_history(self, message: AgentMessage, *, role: str, content: str) -> None:
        history = self._history_items(message)
        history.append({"role": role, "content": content})
        message.metadata["messages"] = history
        self._refresh_conversation_memory(message)

    def _translate_outgoing(
        self,
        *,
        message: AgentMessage,
        texts: list[str],
        follow_up_question: FollowUpQuestion | None,
        actions: list[QuickAction],
    ) -> tuple[list[str], FollowUpQuestion | None, list[QuickAction]]:
        target_language = (message.preferred_language or "en").lower()
        if target_language.startswith("en"):
            return texts, follow_up_question, actions

        source_texts: list[str] = []
        if follow_up_question:
            source_texts.append(follow_up_question.text)
            source_texts.extend(follow_up_question.options)
        source_texts.extend(action.label for action in actions)

        if not source_texts:
            return texts, follow_up_question, actions

        try:
            translated = translate_text_items(texts=source_texts, target_language=target_language)
        except GeminiToolError:
            return texts, follow_up_question, actions

        cursor = 0
        translated_messages = texts

        translated_question = follow_up_question
        if follow_up_question:
            question_text = translated[cursor]
            cursor += 1
            options = translated[cursor : cursor + len(follow_up_question.options)]
            cursor += len(follow_up_question.options)
            translated_question = FollowUpQuestion(
                question_id=follow_up_question.question_id,
                text=question_text,
                kind=follow_up_question.kind,
                options=options,
            )

        translated_actions: list[QuickAction] = []
        for action in actions:
            translated_actions.append(
                QuickAction(label=translated[cursor], intent=action.intent, prompt=action.prompt)
            )
            cursor += 1

        return translated_messages, translated_question, translated_actions

    def _suggested_actions(self, message: AgentMessage, intent: str, follow_up_question: FollowUpQuestion | None = None) -> list[QuickAction]:
        if follow_up_question is not None:
            return []
        state = self._get_state(message)
        actions: list[QuickAction] = []
        if state.stage == "decision":
            actions.append(QuickAction(label="What should I do?", intent="guidance"))
            actions.append(QuickAction(label="Find care near me", intent="care"))
            actions.append(QuickAction(label="Compare cost", intent="cost"))
        elif state.stage == "navigation":
            actions.append(QuickAction(label="Compare cost", intent="cost"))
        elif intent == "guidance":
            actions.append(QuickAction(label="Find care near me", intent="care"))
            actions.append(QuickAction(label="Compare cost", intent="cost"))
        return actions

    def _ui_blocks(self, message: AgentMessage, intent: str) -> list[str]:
        blocks: list[str] = []
        state = self._get_state(message)
        if state.stage in {"decision", "triage"} or intent == "guidance":
            blocks.append("guidance")
        if message.emergency_flag:
            blocks.append("emergency")
        if state.stage == "navigation" and message.hospitals:
            blocks.append("care_options")
        if state.stage == "cost" and message.cost_options:
            blocks.extend(["care_options", "costs"])
        return blocks

    def _stream_chunks(self, request: ChatTurnRequest) -> list[ChatStreamChunk]:
        message = self._session_to_message(request)
        chunks: list[ChatStreamChunk] = []
        current_session = self._message_to_session(message)
        pending_question_before = current_session.pending_question
        if request.message:
            self._append_history(message, role="user", content=request.message)
        state_before = self._get_state(message)
        state = state_before
        answered_by_fallback = False
        meaning = self._extract_semantic_meaning(message, state, pending_question_before)
        meaning = self._reconcile_follow_up_with_known_state(
            state=state,
            meaning=meaning,
            pending_question=pending_question_before,
            message=message,
        )
        if pending_question_before and not meaning.answered_pending_question and meaning.follow_up_needed:
            state, meaning, answered_by_fallback = self._apply_follow_up_fallback(
                pending_question=pending_question_before,
                user_text=request.message or "",
                state=state,
                meaning=meaning,
                message=message,
            )
            if answered_by_fallback:
                append_trace(
                    message,
                    event="tool_called",
                    agent="root_agent",
                    tool="deterministic_followup_resolver",
                    detail="Pending follow-up resolved after semantic extraction fallback.",
                )

        if not pending_question_before and meaning.is_new_case:
            state = self._reset_case_state(message)
            append_trace(
                message,
                event="state_updated",
                agent="root_agent",
                detail="Semantic layer marked this turn as a new clinical case.",
            )
            current_session.pending_question = None

        merged_state = self._merge_state_from_meaning(state, meaning)
        meaning = self._validate_semantic_follow_up(
            state_before=state,
            merged_state=merged_state,
            meaning=meaning,
            pending_question=pending_question_before,
            message=message,
        )
        state = self._merge_state_from_meaning(state, meaning)
        answered_pending = bool(
            pending_question_before
            and request.message
            and (meaning.answered_pending_question or not meaning.follow_up_needed or answered_by_fallback)
        )
        self._record_follow_up_answer(message, pending_question_before, request.message or "", answered_pending)
        message.risk_level = state.risk
        message.risk_reason = (
            f"Semantic urgency assessment indicates {meaning.urgency} urgency "
            f"with severity {meaning.severity}."
        )
        append_trace(
            message,
            event="intent_detected",
            agent="root_agent",
            intent=meaning.intent,
            detail=f"Semantic intent={meaning.intent}, goal={meaning.user_goal}, urgency={meaning.urgency}",
        )

        with trace_span(message, start_event="request_received", finish_event="pipeline_completed", detail=f"Chat intent accepted: {request.intent}"):
            if meaning.symptoms or not message.normalized_text:
                message = self.router.handoff(message, from_agent="root_agent", to_agent="language_agent", intent="normalize_and_translate")
                if meaning.symptoms:
                    state.symptom = self._merge_symptoms(state.symptom, meaning.symptoms, replace=meaning.is_new_case)
                else:
                    state.symptom = state.symptom or message.translated_text or message.normalized_text or message.raw_text

            if (
                meaning.urgency == "high"
                and not message.emergency_flag
                and self._should_trigger_emergency(
                    raw_text=message.raw_text,
                    normalized_text=message.normalized_text or message.translated_text,
                    detected_symptoms=meaning.symptoms,
                    known_symptom=state.symptom,
                )
            ):
                message = self.router.handoff(message, from_agent="root_agent", to_agent="emergency_agent", intent="issue_emergency_guidance")
                state.risk = "high"

            if state.stage == "navigation":
                message.metadata["consent_to_fetch_external"] = True
                message = self.router.handoff(message, from_agent="root_agent", to_agent="navigation_agent", intent="find_nearby_care")

            elif state.stage == "cost":
                message.metadata["consent_to_fetch_external"] = True
                if not message.hospitals:
                    message = self.router.handoff(message, from_agent="root_agent", to_agent="navigation_agent", intent="find_nearby_care")
                message = self.router.handoff(message, from_agent="navigation_agent", to_agent="cost_agent", intent="compare_cost_options")

        follow_up_question = None
        if meaning.follow_up_needed and meaning.urgency != "high" and state.intent not in {"care", "cost"}:
            state.stage = "clarify"
            follow_up_question = self._build_follow_up_from_meaning(meaning)
        elif state.stage == "triage":
            state.stage = "decision"

        message.risk_level = state.risk
        self._set_state(message, state)
        message.metadata["pending_question"] = follow_up_question.model_dump(mode="json") if follow_up_question else None
        session = self._message_to_session(message)
        suggested_actions = self._build_actions(state, meaning, follow_up_question)
        ui_blocks = self._build_ui_blocks(message, state)
        translated_messages, translated_follow_up, translated_actions = self._translate_outgoing(
            message=message,
            texts=[self._generate_reply(message=message, state=state, meaning=meaning, follow_up_question=follow_up_question)],
            follow_up_question=follow_up_question,
            actions=suggested_actions,
        )
        assistant_message = translated_messages[0].strip() if translated_messages else ""
        if assistant_message:
            self._append_history(message, role="assistant", content=assistant_message)
            session = self._message_to_session(message)
        response_payload = AssistantTurnPayload(
            message=assistant_message,
            follow_up=translated_follow_up,
            actions=translated_actions,
            ui_blocks=ui_blocks,
        )
        chosen_action = state.stage
        if message.emergency_flag:
            chosen_action = "emergency"
        elif message.cost_options:
            chosen_action = "cost"
        elif message.hospitals:
            chosen_action = "navigation"
        elif translated_follow_up:
            chosen_action = "follow_up"
        self._log_semantic_turn(
            message=message,
            latest_user_message=request.message or "",
            pending_question=pending_question_before,
            state_before=state_before,
            semantic_meaning=meaning,
            state_after=state,
            chosen_action=chosen_action,
            response_payload=response_payload,
        )
        session_store.set(session.session_id or message.request_id, session)
        chunks.append(
            ChatStreamChunk(
                type="message",
                session_id=session.session_id or message.request_id,
                request_id=message.request_id,
                intent=state.intent if state.intent in {"symptoms", "guidance", "care", "cost"} else request.intent,
                message=assistant_message,
                response=response_payload,
            )
        )
        chunks.append(
            ChatStreamChunk(
                type="done",
                session_id=session.session_id or message.request_id,
                request_id=message.request_id,
                intent=state.intent if state.intent in {"symptoms", "guidance", "care", "cost"} else request.intent,
                session=session,
                message=None,
                ui_blocks=ui_blocks,
                suggested_actions=translated_actions,
                follow_up_question=translated_follow_up,
                response=response_payload,
                trace=message.trace,
                agent_flow=build_agent_flow(message),
            )
        )
        return chunks

    def run_pipeline(self, request: AnalyzeRequest) -> AnalyzeResponse:
        message = AgentMessage(
            user_id=request.user_id,
            location=request.location,
            raw_text=request.text,
            preferred_language=request.preferred_language,
            metadata={"use_adk": self.use_adk},
        )

        with trace_span(message, start_event="request_received", finish_event="pipeline_completed", detail="Analyze request accepted"):
            message = self.router.handoff(message, from_agent="root_agent", to_agent="language_agent", intent="normalize_and_translate")
            message = self.router.handoff(message, from_agent="language_agent", to_agent="triage_agent", intent="assess_urgency")

            if self._should_trigger_emergency(
                raw_text=message.raw_text,
                normalized_text=message.normalized_text or message.translated_text,
            ):
                message = self.router.handoff(message, from_agent="triage_agent", to_agent="emergency_agent", intent="issue_emergency_guidance")

            message = self.router.handoff(message, from_agent="triage_agent", to_agent="navigation_agent", intent="find_nearby_care")
            message = self.router.handoff(message, from_agent="navigation_agent", to_agent="cost_agent", intent="compare_cost_options")
            message = self.router.handoff(message, from_agent="cost_agent", to_agent="contact_agent", intent="prepare_provider_handoff")

        return build_response(message)

    def run_chat_turn(self, request: ChatTurnRequest) -> ChatTurnResponse:
        chunks = self._stream_chunks(request)
        final = chunks[-1]
        message_list = [chunk.message for chunk in chunks if chunk.type == "message" and chunk.message]
        assert final.session is not None
        return ChatTurnResponse(
            session_id=final.session.session_id or final.request_id,
            request_id=final.request_id,
            intent=request.intent,
            session=final.session,
            state=final.session.state,
            assistant_message="\n\n".join(message_list).strip(),
            ui_blocks=final.ui_blocks,
            suggested_actions=final.suggested_actions,
            follow_up_question=final.follow_up_question,
            response=final.response,
            trace=final.trace,
            agent_flow=final.agent_flow,
        )

    def stream_chat_turn(self, request: ChatTurnRequest) -> list[ChatStreamChunk]:
        return self._stream_chunks(request)

    def get_chat_session(self, session_id: str) -> ChatSessionState | None:
        return session_store.get(session_id)

    def run_communication(self, summary: SummaryOutput) -> CommunicationResponse:
        message = AgentMessage(
            location=summary.location,
            raw_text=summary.patient_input,
            detected_language=summary.detected_language,
            normalized_text=summary.normalized_text,
            translated_text=summary.normalized_text,
            risk_level=summary.risk_level,
            risk_reason=summary.triage_explanation,
            emergency_flag=summary.emergency_flag,
            emergency_instructions=summary.emergency_instructions,
        )
        provider_message = format_provider_message(message)
        append_trace(message, event="agent_completed", agent="contact_agent", detail="Provider message composed from summary")
        return CommunicationResponse(message=provider_message)


orchestrator = HealthcareOrchestrator()


def run_analysis(request: AnalyzeRequest) -> AnalyzeResponse:
    return orchestrator.run_pipeline(request)


def run_communication(summary: SummaryOutput) -> CommunicationResponse:
    return orchestrator.run_communication(summary)


def run_chat_turn(request: ChatTurnRequest) -> ChatTurnResponse:
    return orchestrator.run_chat_turn(request)


def stream_chat_turn(request: ChatTurnRequest) -> list[ChatStreamChunk]:
    return orchestrator.stream_chat_turn(request)


def get_chat_session(session_id: str) -> ChatSessionState | None:
    return orchestrator.get_chat_session(session_id)
