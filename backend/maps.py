import os
from typing import Any
from urllib.parse import quote_plus

import httpx
from dotenv import load_dotenv

load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")


async def get_nearby_hospitals(lat: float, lng: float) -> list[dict[str, Any]]:
    if not GOOGLE_API_KEY:
        return []

    params = {
        "location": f"{lat},{lng}",
        "radius": 5000,
        "type": "hospital",
        "key": GOOGLE_API_KEY,
    }
    url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            payload = response.json()
    except httpx.HTTPError:
        return []

    hospitals: list[dict[str, Any]] = []
    for item in payload.get("results", [])[:3]:
        geo = item.get("geometry", {}).get("location", {})
        place_id = str(item.get("place_id", ""))
        hospital_lat = geo.get("lat")
        hospital_lng = geo.get("lng")
        directions_url = ""
        if hospital_lat is not None and hospital_lng is not None:
            directions_url = (
                "https://www.google.com/maps/dir/?api=1"
                f"&destination={hospital_lat},{hospital_lng}"
            )

        hospitals.append(
            {
                "id": place_id,
                "name": item.get("name", "Unknown Hospital"),
                "address": item.get("vicinity", item.get("formatted_address", "Address unavailable")),
                "location": {
                    "lat": hospital_lat,
                    "lng": hospital_lng,
                },
                "directions_url": directions_url,
                "booking_url": (
                    "https://mock-booking-portal.com/schedule?facility_id="
                    f"{quote_plus(place_id)}"
                ),
            }
        )

    return hospitals
