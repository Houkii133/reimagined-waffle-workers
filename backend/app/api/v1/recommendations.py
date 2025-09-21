"""Recommendation endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlmodel import select

from ai_job_matcher import Feedback as EngineFeedback

from app.auth.dependencies import get_current_active_user
from app.db.session import get_session
from app.models.job import FeedbackEvent
from app.models.user import User, UserProfile
from app.schemas.recommendation import (
    FeedbackRequest,
    MatchRecommendation,
    RecommendationList,
    WhatIfRequest,
    WhatIfResponse,
    WhyNotResponse,
)
from app.services import engine_service

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


@router.get("", response_model=RecommendationList)
async def get_recommendations(
    top_k: int = 20,
    session=Depends(get_session),
    current_user: User = Depends(get_current_active_user),
):
    profile_result = await session.exec(select(UserProfile).where(UserProfile.user_id == current_user.id))
    profile = profile_result.one_or_none()
    recs = engine_service.recommend(current_user, profile, top_k=top_k)
    return RecommendationList(items=[MatchRecommendation.model_validate(rec.__dict__) for rec in recs])


@router.post("/feedback")
async def send_feedback(
    payload: FeedbackRequest,
    session=Depends(get_session),
    current_user: User = Depends(get_current_active_user),
):
    feedback = FeedbackEvent(
        user_id=current_user.id,
        job_id=payload.job_id,
        event_type=payload.event_type,
        event_metadata=payload.metadata or {},
    )
    session.add(feedback)
    await session.commit()
    engine_service.record_feedback(
        EngineFeedback(user_id=current_user.id, job_id=payload.job_id, event_type=payload.event_type, metadata=payload.metadata)
    )
    return {"status": "accepted"}


@router.get("/why_not/{job_id}", response_model=WhyNotResponse)
async def why_not(job_id: int, session=Depends(get_session), current_user: User = Depends(get_current_active_user)):
    profile_result = await session.exec(select(UserProfile).where(UserProfile.user_id == current_user.id))
    profile = profile_result.one_or_none()
    result = engine_service.why_not(current_user, profile, job_id)
    return WhyNotResponse.model_validate(result)


@router.post("/what_if", response_model=WhatIfResponse)
async def what_if(
    payload: WhatIfRequest,
    session=Depends(get_session),
    current_user: User = Depends(get_current_active_user),
):
    profile_result = await session.exec(select(UserProfile).where(UserProfile.user_id == current_user.id))
    profile = profile_result.one_or_none()
    recs = engine_service.what_if(current_user, profile, payload.changes)
    return WhatIfResponse(items=[MatchRecommendation.model_validate(rec.__dict__) for rec in recs])
