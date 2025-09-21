"""Admin endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlmodel import select

from app.auth.dependencies import get_current_admin
from app.db.session import get_session
from app.models.job import FeatureFlag
from app.schemas.admin import FeatureFlagUpdate, TelemetryResponse
from app.services import engine_service
from app.tasks.jobs import ingest_all_jobs, _ingest_all_jobs_sync

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/telemetry", response_model=TelemetryResponse)
async def get_telemetry(admin=Depends(get_current_admin)):
    data = engine_service.telemetry()
    return TelemetryResponse(**data)


@router.post("/reindex")
async def reindex(admin=Depends(get_current_admin)):
    try:
        ingest_all_jobs.delay()
    except Exception:  # pragma: no cover
        _ingest_all_jobs_sync()
    return {"status": "queued"}


@router.post("/feature_flags")
async def update_feature_flag(payload: FeatureFlagUpdate, session=Depends(get_session), admin=Depends(get_current_admin)):
    existing = await session.exec(select(FeatureFlag).where(FeatureFlag.key == payload.key))
    flag = existing.one_or_none()
    if not flag:
        flag = FeatureFlag(key=payload.key)
    flag.enabled = payload.enabled
    flag.payload = payload.payload or {}
    session.add(flag)
    await session.commit()
    await session.refresh(flag)
    return {"status": "updated"}
