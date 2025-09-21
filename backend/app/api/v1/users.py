"""User endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlmodel import select

from app.auth.dependencies import get_current_active_user
from app.db.session import get_session
from app.models.user import User, UserProfile
from app.schemas.user import UserRead, UserUpdate

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserRead)
async def read_current_user(current_user: User = Depends(get_current_active_user)):
    return current_user


@router.put("/me", response_model=UserRead)
async def update_current_user(
    payload: UserUpdate,
    session=Depends(get_session),
    current_user: User = Depends(get_current_active_user),
):
    if payload.full_name:
        current_user.full_name = payload.full_name
    result = await session.exec(select(UserProfile).where(UserProfile.user_id == current_user.id))
    profile = result.one_or_none()
    if not profile:
        profile = UserProfile(
            user_id=current_user.id,
            skills=[],
            soft_skills=[],
            desired_roles=[],
            desired_industries=[],
            location_preferences=[],
        )
        session.add(profile)
    update_data = payload.dict(exclude_unset=True)
    for field, value in update_data.items():
        if hasattr(profile, field):
            setattr(profile, field, value)
    session.add(current_user)
    session.add(profile)
    await session.commit()
    await session.refresh(current_user)
    return current_user
