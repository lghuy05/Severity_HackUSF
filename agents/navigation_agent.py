from agents.core.base_agent import create_agent
from shared.schemas import HospitalLocation, NavigationOutput


MOCK_HOSPITALS = [
    HospitalLocation(
        name="Mercy General Hospital",
        address="1200 Market St",
        lat=37.7749,
        lng=-122.4194,
        phone="(415) 555-0101",
    ),
    HospitalLocation(
        name="Community Care Medical Center",
        address="800 Mission St",
        lat=37.7840,
        lng=-122.4075,
        phone="(415) 555-0130",
    ),
    HospitalLocation(
        name="Starlight Emergency Clinic",
        address="220 Howard St",
        lat=37.7897,
        lng=-122.3942,
        phone="(415) 555-0188",
    ),
]


def find_nearby_hospitals(risk_level: str, location: str) -> NavigationOutput:
    recommendation = (
        "Head to the nearest emergency department now."
        if risk_level == "high"
        else "Here are nearby care options based on your location."
    )
    return NavigationOutput(
        origin=location,
        recommendation=recommendation,
        hospitals=MOCK_HOSPITALS,
    )


def _navigation_handler(message, _context) -> NavigationOutput:
    payload = message if isinstance(message, dict) else {}
    return find_nearby_hospitals(
        risk_level=str(payload.get("risk_level", "low")),
        location=str(payload.get("location", "Unknown location")),
    )


navigation_agent = create_agent(
    key="navigation",
    name="navigation_agent",
    instruction=(
        "Suggest hospitals or care sites based on risk and location. "
        "For high-risk cases, direct the user toward the nearest emergency department."
    ),
    handler=_navigation_handler,
    metadata={"role": "care_navigation"},
)
