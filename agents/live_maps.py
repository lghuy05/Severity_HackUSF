"""
Live Maps Agent -- uses Google Places API (Nearby Search)
to find hospitals near the user's location.

Returns a list of up to 3 simplified hospital dicts:
    [
        {
            "name": "Tampa General Hospital",
            "address": "1 Tampa General Cir, Tampa, FL 33606",
            "lat": 27.9396,
            "lng": -82.4572,
        },
        ...
    ]
"""

import os
from typing import List

import httpx

PLACES_URL = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
SEARCH_RADIUS = 5000  # 5 km
MAX_RESULTS = 3


async def get_nearby_hospitals(lat: float, lng: float) -> List[dict]:
    """
    Query Google Places Nearby Search for hospitals within 5 km.

    Parameters
    ----------
    lat, lng : float
        The user's latitude and longitude.

    Returns
    -------
    list[dict]  -- up to 3 hospitals with name, address, lat, lng.
    """
    api_key = os.getenv("GOOGLE_API_KEY", "")
    if not api_key:
        print("[WARN] GOOGLE_API_KEY not set -- returning empty hospital list.")
        return []

    params = {
        "location": f"{lat},{lng}",
        "radius": SEARCH_RADIUS,
        "type": "hospital",
        "key": api_key,
    }

    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.get(PLACES_URL, params=params)
            resp.raise_for_status()
            data = resp.json()

        results = data.get("results", [])[:MAX_RESULTS]

        hospitals = []
        for place in results:
            loc = place.get("geometry", {}).get("location", {})
            hospitals.append({
                "name": place.get("name", "Unknown"),
                "address": place.get("vicinity", place.get("formatted_address", "Unknown")),
                "lat": loc.get("lat", 0.0),
                "lng": loc.get("lng", 0.0),
            })

        return hospitals

    except Exception as exc:
        print(f"[WARN] Places API error: {exc}")
        return []
