"""Wrapper around the AI job matching engine."""
from __future__ import annotations

from functools import lru_cache
from typing import Iterable, List

from ai_job_matcher import Feedback as EngineFeedback
from ai_job_matcher import JobMatchEngine, JobPosting as EngineJob
from ai_job_matcher import MatchRecommendation as EngineRecommendation
from ai_job_matcher import UserProfile as EngineUserProfile

from app.models.job import Job
from app.models.user import User, UserProfile


@lru_cache
def get_engine() -> JobMatchEngine:
    return JobMatchEngine()


def map_job(job: Job) -> EngineJob:
    return EngineJob(
        id=job.id or 0,
        title=job.title,
        description=job.description,
        company=job.company_name,
        location=job.location,
        modality=job.modality,
        salary_min=job.salary_min,
        salary_max=job.salary_max,
        skills=job.skills,
        industry=job.industry,
        seniority=job.seniority,
        company_size=job.company_size,
    )


def map_user_profile(user: User, profile: UserProfile | None) -> EngineUserProfile:
    profile = profile or UserProfile(
        user_id=user.id or 0,
        skills=[],
        soft_skills=[],
        desired_roles=[],
        desired_industries=[],
        location_preferences=[],
    )
    return EngineUserProfile(
        id=user.id or 0,
        email=user.email,
        skills=profile.skills + profile.soft_skills,
        years_experience=profile.years_experience,
        desired_roles=profile.desired_roles,
        desired_industries=profile.desired_industries,
        salary_expectations={
            "currency": profile.salary_currency,
            "min": profile.salary_min,
            "max": profile.salary_max,
        },
        location_preferences=profile.location_preferences,
        work_authorization=profile.work_authorization,
        career_goals=profile.career_goals,
    )


def ingest_jobs(jobs: Iterable[Job]) -> None:
    engine = get_engine()
    engine.ingest_jobs([map_job(job) for job in jobs])


def recommend(user: User, profile: UserProfile | None, top_k: int = 20) -> List[EngineRecommendation]:
    engine = get_engine()
    engine_profile = map_user_profile(user, profile)
    return engine.recommend(engine_profile, top_k=top_k)


def record_feedback(feedback: EngineFeedback) -> None:
    engine = get_engine()
    engine.record_feedback(feedback)


def why_not(user: User, profile: UserProfile | None, job_id: int):
    engine = get_engine()
    engine_profile = map_user_profile(user, profile)
    return engine.why_not(engine_profile, job_id)


def what_if(user: User, profile: UserProfile | None, changes: dict):
    engine = get_engine()
    engine_profile = map_user_profile(user, profile)
    return engine.what_if(engine_profile, changes)


def telemetry() -> dict:
    return get_engine().telemetry
