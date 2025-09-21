"""Background tasks for job ingestion and recommendation refresh."""
from __future__ import annotations

from celery import shared_task
from sqlmodel import Session, select

from app.db.session import sync_engine
from app.models.job import Job
from app.services import engine_service


def _ingest_job_sync(job_id: int) -> None:
    with Session(sync_engine) as session:
        result = session.exec(select(Job).where(Job.id == job_id))
        job = result.one_or_none()
        if job:
            engine_service.ingest_jobs([job])


def _ingest_all_jobs_sync() -> None:
    with Session(sync_engine) as session:
        jobs = session.exec(select(Job)).all()
        engine_service.ingest_jobs(jobs)


@shared_task
def ingest_job(job_id: int) -> None:
    _ingest_job_sync(job_id)


@shared_task
def ingest_all_jobs() -> None:
    _ingest_all_jobs_sync()


__all__ = ["ingest_job", "ingest_all_jobs", "_ingest_job_sync", "_ingest_all_jobs_sync"]
