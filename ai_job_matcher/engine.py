"""Simplified local stub of JobMatchEngine.

This implementation is intentionally lightweight while mimicking the API surface
required by the application. It should be replaced with the production engine
in real deployments.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Sequence


@dataclass
class UserProfile:
    id: int
    email: str
    skills: List[str] = field(default_factory=list)
    years_experience: int | None = None
    desired_roles: List[str] = field(default_factory=list)
    desired_industries: List[str] = field(default_factory=list)
    salary_expectations: Dict[str, Any] | None = None
    location_preferences: List[str] = field(default_factory=list)
    work_authorization: str | None = None
    career_goals: str | None = None


@dataclass
class JobPosting:
    id: int
    title: str
    description: str
    company: str
    location: str
    modality: str
    salary_min: int | None = None
    salary_max: int | None = None
    skills: List[str] = field(default_factory=list)
    industry: str | None = None
    seniority: str | None = None
    company_size: str | None = None


@dataclass
class MatchRecommendation:
    job_id: int
    score: float
    rationale: List[str] = field(default_factory=list)
    fit_dimensions: Dict[str, float] = field(default_factory=dict)
    qualification_gaps: List[str] = field(default_factory=list)


@dataclass
class Feedback:
    user_id: int
    job_id: int
    event_type: str
    metadata: Dict[str, Any] | None = None


class JobMatchEngine:
    """Toy recommendation engine.

    Recommendations are generated based on overlapping skills.
    """

    def __init__(self) -> None:
        self._jobs: Dict[int, JobPosting] = {}
        self._feedback: List[Feedback] = []

    def ingest_jobs(self, jobs: Iterable[JobPosting]) -> None:
        for job in jobs:
            self._jobs[job.id] = job

    def recommend(self, user_profile: UserProfile, top_k: int = 20) -> List[MatchRecommendation]:
        recs: List[MatchRecommendation] = []
        user_skills = set(skill.lower() for skill in user_profile.skills)
        for job in self._jobs.values():
            job_skills = set(skill.lower() for skill in job.skills)
            overlap = user_skills.intersection(job_skills)
            score = len(overlap) / max(len(job_skills) or 1, 1)
            rationale = [f"Matches skill: {skill}" for skill in sorted(overlap)]
            gaps = sorted(job_skills - overlap)
            recs.append(
                MatchRecommendation(
                    job_id=job.id,
                    score=round(score, 3),
                    rationale=rationale or ["Explore new opportunity"],
                    fit_dimensions={"skill_fit": round(score, 3)},
                    qualification_gaps=[f"Missing skill: {gap}" for gap in gaps],
                )
            )
        recs.sort(key=lambda rec: rec.score, reverse=True)
        return recs[:top_k]

    def record_feedback(self, feedback: Feedback) -> None:
        self._feedback.append(feedback)

    def why_not(self, user_profile: UserProfile, job_id: int) -> Dict[str, Any]:
        job = self._jobs.get(job_id)
        if not job:
            return {"reason": "Job not found"}
        user_skills = set(skill.lower() for skill in user_profile.skills)
        job_skills = set(skill.lower() for skill in job.skills)
        missing = sorted(job_skills - user_skills)
        return {
            "job_id": job_id,
            "missing_skills": missing,
            "message": "Add these skills to improve your fit.",
        }

    def what_if(self, user_profile: UserProfile, changes: Dict[str, Any]) -> List[MatchRecommendation]:
        simulated_profile = UserProfile(**{**user_profile.__dict__, **changes})
        return self.recommend(simulated_profile)

    @property
    def telemetry(self) -> Dict[str, Any]:
        return {
            "jobs_indexed": len(self._jobs),
            "feedback_events": len(self._feedback),
        }
