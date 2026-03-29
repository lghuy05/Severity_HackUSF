from __future__ import annotations

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel

from backend.schemas import UserProfile
from backend.user_profile_service import get_or_create_profile, update_profile


router = APIRouter(prefix="/user", tags=["user-profile"])


class UserProfileUpdateRequest(BaseModel):
    name: str | None = None
    language: str | None = None
    location: str | None = None
    age: int | None = None
    gender: str | None = None


def _require_user_id(x_user_id: str | None) -> str:
    user_id = (x_user_id or "").strip()
    if not user_id:
        raise HTTPException(status_code=400, detail="Missing x-user-id header")
    return user_id


@router.get("/profile", response_model=UserProfile)
def get_user_profile(x_user_id: str | None = Header(default=None, alias="x-user-id")) -> UserProfile:
    return get_or_create_profile(_require_user_id(x_user_id))


@router.post("/profile", response_model=UserProfile)
def update_user_profile(
    request: UserProfileUpdateRequest,
    x_user_id: str | None = Header(default=None, alias="x-user-id"),
) -> UserProfile:
    patch = request.model_dump(exclude_unset=True)
    return update_profile(_require_user_id(x_user_id), patch)
