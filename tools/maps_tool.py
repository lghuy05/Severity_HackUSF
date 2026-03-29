from __future__ import annotations

import json
import os
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from backend.schemas import AgentMessage, HospitalLocation
from tools.cache_utils import TTLCache

PLACES_TEXT_SEARCH_ENDPOINT = "https://places.googleapis.com/v1/places:searchText"
MAPS_CACHE = TTLCache(ttl_seconds=300)


def find_nearby_services(message: AgentMessage) -> list[HospitalLocation]:
    cache_key = f"{message.location}|{message.risk_level}|{message.preferred_language or 'en'}"
    return MAPS_CACHE.get_or_set(cache_key, lambda: _fetch_nearby_services(message))


def _fetch_nearby_services(message: AgentMessage) -> list[HospitalLocation]:
    google_maps_key = os.getenv("GOOGLE_MAPS_API_KEY", "")
    if not google_maps_key:
        return []

    query = _build_places_query(message)
    request_body = {
        "textQuery": query,
        "maxResultCount": 5,
        "languageCode": "en",
    }
    request = Request(
        PLACES_TEXT_SEARCH_ENDPOINT,
        data=json.dumps(request_body).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "X-Goog-Api-Key": google_maps_key,
            "X-Goog-FieldMask": (
                "places.displayName,"
                "places.formattedAddress,"
                "places.location,"
                "places.nationalPhoneNumber,"
                "places.googleMapsUri,"
                "places.currentOpeningHours.openNow"
            ),
        },
        method="POST",
    )

    try:
        with urlopen(request, timeout=20) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError):  # pragma: no cover - remote dependency
        return []

    places = payload.get("places", [])
    return [_to_hospital_location(place) for place in places if _is_complete_place(place)]


def _build_places_query(message: AgentMessage) -> str:
    if message.risk_level == "high":
        return f"emergency room or hospital near {message.location}"
    if message.risk_level == "medium":
        return f"urgent care clinic or hospital near {message.location}"
    return f"community health clinic or urgent care near {message.location}"


def _to_hospital_location(place: dict[str, Any]) -> HospitalLocation:
    location = place.get("location", {})
    opening_hours = place.get("currentOpeningHours", {})
    display_name = place.get("displayName", {})
    return HospitalLocation(
        name=display_name.get("text", "Unknown facility"),
        address=place.get("formattedAddress", ""),
        lat=float(location.get("latitude", 0.0)),
        lng=float(location.get("longitude", 0.0)),
        phone=place.get("nationalPhoneNumber", ""),
        open_now=bool(opening_hours.get("openNow", False)),
        google_maps_uri=place.get("googleMapsUri"),
    )


def _is_complete_place(place: dict[str, Any]) -> bool:
    location = place.get("location", {})
    return bool(place.get("formattedAddress")) and "latitude" in location and "longitude" in location
