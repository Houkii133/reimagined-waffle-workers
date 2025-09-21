from __future__ import annotations

from fastapi.testclient import TestClient
from sqlmodel import Session

from app.auth.security import get_password_hash
from app.db.session import sync_engine
from app.models.job import Job
from app.models.user import Employer, User, UserProfile
from app.services.engine_service import ingest_jobs


def create_candidate(session: Session) -> User:
    user = User(email="candidate@example.com", hashed_password=get_password_hash("secret"), role="candidate")
    session.add(user)
    session.commit()
    session.refresh(user)
    profile = UserProfile(
        user_id=user.id,
        skills=["python", "fastapi"],
        soft_skills=["communication"],
        desired_roles=["backend"],
        desired_industries=["tech"],
        location_preferences=["remote"],
    )
    session.add(profile)
    session.commit()
    return user


def create_job(session: Session, employer: Employer, **kwargs) -> Job:
    job = Job(
        employer_id=employer.id,
        company_name=employer.company_name,
        title="Backend Engineer",
        description="Work on APIs",
        location="Remote",
        modality="remote",
        skills=["Python", "FastAPI"],
        responsibilities=["Build APIs"],
        requirements=["3+ years"],
        culture_signals=["Collaborative"],
        growth_signals=["Series B"],
        **kwargs,
    )
    session.add(job)
    session.commit()
    session.refresh(job)
    return job


def setup_employer(session: Session) -> Employer:
    employer_user = User(email="employer@example.com", hashed_password=get_password_hash("secret"), role="employer", full_name="Acme")
    session.add(employer_user)
    session.commit()
    session.refresh(employer_user)
    employer = Employer(user_id=employer_user.id, company_name="Acme Corp")
    session.add(employer)
    session.commit()
    session.refresh(employer)
    return employer


def test_recommendations_flow(client: TestClient) -> None:
    with Session(sync_engine) as session:
        candidate = create_candidate(session)
        employer = setup_employer(session)
        job = create_job(session, employer)
        ingest_jobs([job])

    login_resp = client.post("/api/v1/auth/login", data={"username": "candidate@example.com", "password": "secret"})
    assert login_resp.status_code == 200, login_resp.text
    token = login_resp.json()["access_token"]

    rec_resp = client.get("/api/v1/recommendations", headers={"Authorization": f"Bearer {token}"})
    assert rec_resp.status_code == 200
    items = rec_resp.json()["items"]
    assert items, "Recommendations should not be empty"
    feedback_payload = {"job_id": items[0]["job_id"], "event_type": "save"}
    feedback_resp = client.post("/api/v1/recommendations/feedback", json=feedback_payload, headers={"Authorization": f"Bearer {token}"})
    assert feedback_resp.status_code == 200
