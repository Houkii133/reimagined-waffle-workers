"""Authentication endpoints."""
from __future__ import annotations

from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import select

from app.auth.security import create_access_token, get_password_hash, verify_password
from app.db.session import get_session
from app.models.user import User, UserProfile
from app.schemas.auth import RegisterRequest, Token
from app.schemas.user import UserRead

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register_user(payload: RegisterRequest, session=Depends(get_session)):
    existing = await session.exec(select(User).where(User.email == payload.email))
    if existing.one_or_none():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    user = User(
        email=payload.email,
        hashed_password=get_password_hash(payload.password),
        full_name=payload.full_name,
        role=payload.role,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    if user.role == "candidate":
        profile = UserProfile(
            user_id=user.id,
            skills=[],
            soft_skills=[],
            desired_roles=[],
            desired_industries=[],
            location_preferences=[],
        )
        session.add(profile)
        await session.commit()
        await session.refresh(user)
    return user


@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), session=Depends(get_session)):
    result = await session.exec(select(User).where(User.email == form_data.username))
    user = result.one_or_none()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect credentials")
    token = create_access_token(str(user.id), expires_delta=timedelta(minutes=60))
    return Token(access_token=token)


@router.post("/logout")
async def logout():
    return {"status": "ok"}
