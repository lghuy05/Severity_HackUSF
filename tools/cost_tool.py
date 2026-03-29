from __future__ import annotations

from backend.schemas import AgentMessage, CostOption
from tools.cache_utils import TTLCache
from tools.gemini_tool import GeminiToolError, estimate_costs_with_gemini

COST_CACHE = TTLCache(ttl_seconds=300)


def compare_care_costs(message: AgentMessage) -> list[CostOption]:
    facility_names = ",".join(facility.name for facility in message.hospitals[:5])
    cache_key = f"{message.location}|{message.risk_level}|{facility_names}"
    return COST_CACHE.get_or_set(cache_key, lambda: _compute_costs(message))


def _compute_costs(message: AgentMessage) -> list[CostOption]:
    try:
        payload = estimate_costs_with_gemini(message)
        options = payload.get("cost_options", [])
        if options:
            return [CostOption(**option) for option in options]
    except (GeminiToolError, TypeError, ValueError, KeyError):
        pass

    return _fallback_costs(message)


def _fallback_costs(message: AgentMessage) -> list[CostOption]:
    urgent = message.risk_level == "high"
    facilities = message.hospitals[:5] or []
    if not facilities:
        return [
            CostOption(
                provider="Regional care option",
                care_type="Emergency Department" if urgent else "Urgent Care",
                estimated_cost="$1,200-$3,500" if urgent else "$180-$450",
                estimated_wait="20-60 min" if urgent else "15-45 min",
                coverage_summary="Commercial insurance may reduce patient responsibility; self-pay varies widely.",
                notes="Fallback estimate without facility-specific live pricing context.",
                source="fallback-estimator",
            )
        ]

    options: list[CostOption] = []
    for facility in facilities:
        lower_name = facility.name.lower()
        is_emergency = urgent or "emergency" in lower_name or " er" in lower_name
        options.append(
            CostOption(
                provider=facility.name,
                care_type="Emergency Department" if is_emergency else "Hospital / Urgent Care",
                estimated_cost="$1,200-$3,500" if is_emergency else "$180-$450",
                estimated_wait="20-60 min" if is_emergency else "15-45 min",
                coverage_summary="Insurance acceptance and patient cost vary by plan and deductible.",
                notes="Estimate derived from facility type and urgency when live LLM pricing output is unavailable.",
                source="fallback-estimator",
            )
        )
    return options
