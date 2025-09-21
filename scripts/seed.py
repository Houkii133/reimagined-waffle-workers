"""Seed database with demo data."""
from __future__ import annotations

import random
import sys
from pathlib import Path
from typing import List

sys.path.append(str(Path(__file__).resolve().parents[1] / "backend"))

from sqlmodel import Session, select  # type: ignore  # noqa: E402

from app.db.session import sync_engine  # type: ignore  # noqa: E402
from app.models import Employer, Job, User, UserProfile  # type: ignore  # noqa: E402
from app.services.engine_service import ingest_jobs  # type: ignore  # noqa: E402
from app.auth.security import get_password_hash  # type: ignore  # noqa: E402

SKILLS = ["Python", "React", "FastAPI", "SQL", "Tailwind", "Docker", "AWS", "Kubernetes"]
ROLES = ["Software Engineer", "Product Manager", "Data Scientist"]
INDUSTRIES = ["Fintech", "Healthtech", "E-commerce"]


def ensure_candidate(session: Session, idx: int) -> User:
    email = f"candidate{idx}@example.com"
    user = session.exec(select(User).where(User.email == email)).one_or_none()
    if user:
        return user
    user = User(email=email, hashed_password=get_password_hash("password"), role="candidate", full_name=f"Candidate {idx}")
    session.add(user)
    session.commit()
    session.refresh(user)
    profile = UserProfile(
        user_id=user.id,
        skills=random.sample(SKILLS, k=3),
        soft_skills=["Collaboration", "Communication"],
        desired_roles=[random.choice(ROLES)],
        desired_industries=[random.choice(INDUSTRIES)],
        location_preferences=["Remote"],
    )
    session.add(profile)
    session.commit()
    return user


def ensure_employer(session: Session, idx: int) -> Employer:
    email = f"employer{idx}@example.com"
    user = session.exec(select(User).where(User.email == email)).one_or_none()
    if not user:
        user = User(email=email, hashed_password=get_password_hash("password"), role="employer", full_name=f"Employer {idx}")
        session.add(user)
        session.commit()
        session.refresh(user)
    employer = session.exec(select(Employer).where(Employer.user_id == user.id)).one_or_none()
    if employer:
        return employer
    employer = Employer(user_id=user.id, company_name=f"Company {idx}")
    session.add(employer)
    session.commit()
    session.refresh(employer)
    return employer


def create_job(session: Session, employer: Employer, idx: int) -> Job:
    job = Job(
        employer_id=employer.id,
        company_name=employer.company_name,
        title=f"{random.choice(ROLES)} {idx}",
        description="Build impactful products with a collaborative team.",
        location="Remote",
        modality="remote",
        salary_min=90000,
        salary_max=140000,
        skills=random.sample(SKILLS, k=4),
        responsibilities=["Lead feature development", "Collaborate with cross-functional teams"],
        requirements=["5+ years experience", "Strong problem solving"],
        culture_signals=["Inclusive", "Mentorship"],
        growth_signals=["Series B", "High growth"],
    )
    session.add(job)
    session.commit()
    session.refresh(job)
    return job


def run() -> None:
    with Session(sync_engine) as session:
        jobs: List[Job] = []
        for idx in range(1, 11):
            ensure_candidate(session, idx)
            employer = ensure_employer(session, idx)
            jobs.append(create_job(session, employer, idx))
        ingest_jobs(jobs)
        print("Seeded demo data.")


if __name__ == "__main__":
    run()
