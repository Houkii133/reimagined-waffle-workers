"""Job endpoints."""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlmodel import select

from app.auth.dependencies import get_current_active_user
from app.db.session import get_session
from app.models.job import Job
from app.models.user import Employer, User
from app.schemas.job import JobCreate, JobListResponse, JobRead, JobUpdate
from app.services import engine_service
from app.tasks.jobs import ingest_job

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("", response_model=JobListResponse)
async def list_jobs(
    session=Depends(get_session),
    role: Optional[str] = None,
    location: Optional[str] = None,
    modality: Optional[str] = None,
    skill: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
):
    query = select(Job).where(Job.is_active == True)  # noqa: E712
    if modality:
        query = query.where(Job.modality == modality)
    if location:
        query = query.where(Job.location.ilike(f"%{location}%"))
    if role:
        query = query.where(Job.title.ilike(f"%{role}%"))
    result = await session.exec(query)
    all_items = result.all()
    if skill:
        all_items = [job for job in all_items if skill.lower() in {s.lower() for s in job.skills}]
    total = len(all_items)
    items = all_items[offset : offset + limit]
    return JobListResponse(total=total, items=items)


@router.get("/{job_id}", response_model=JobRead)
async def get_job(job_id: int, session=Depends(get_session)):
    result = await session.exec(select(Job).where(Job.id == job_id))
    job = result.one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.post("/employer/jobs", response_model=JobRead)
async def create_job(
    payload: JobCreate,
    session=Depends(get_session),
    user: User = Depends(get_current_active_user),
):
    if user.role != "employer":
        raise HTTPException(status_code=403, detail="Employer access required")
    result = await session.exec(select(Employer).where(Employer.user_id == user.id))
    employer = result.one_or_none()
    if not employer:
        employer = Employer(user_id=user.id, company_name=user.full_name or "Company")
        session.add(employer)
        await session.commit()
        await session.refresh(employer)
    job = Job(employer_id=employer.id, company_name=employer.company_name, **payload.dict())
    session.add(job)
    await session.commit()
    await session.refresh(job)
    try:
        ingest_job.delay(job.id)
    except Exception:  # pragma: no cover - fallback when broker unavailable
        engine_service.ingest_jobs([job])
    return job


@router.put("/employer/jobs/{job_id}", response_model=JobRead)
async def update_job(
    job_id: int,
    payload: JobUpdate,
    session=Depends(get_session),
    user: User = Depends(get_current_active_user),
):
    result = await session.exec(select(Job).where(Job.id == job_id))
    job = result.one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    employer_result = await session.exec(select(Employer).where(Employer.user_id == user.id))
    employer = employer_result.one_or_none()
    if not employer or job.employer_id != employer.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    for field, value in payload.dict(exclude_unset=True).items():
        setattr(job, field, value)
    job.company_name = employer.company_name
    session.add(job)
    await session.commit()
    await session.refresh(job)
    try:
        ingest_job.delay(job.id)
    except Exception:  # pragma: no cover - fallback when broker unavailable
        engine_service.ingest_jobs([job])
    return job


@router.post("/employer/jobs:bulk_import")
async def bulk_import_jobs(
    file: UploadFile = File(...),
    session=Depends(get_session),
    user: User = Depends(get_current_active_user),
):
    if user.role != "employer":
        raise HTTPException(status_code=403, detail="Employer access required")
    content = await file.read()
    # This mock simply acknowledges receipt; real implementation would parse
    return {"status": "queued", "bytes_received": len(content)}
