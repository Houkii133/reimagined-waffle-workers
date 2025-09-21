"""Synthetic dataset generator for testing."""

from __future__ import annotations

import random
from dataclasses import dataclass
from datetime import date, timedelta
from typing import List

from .data_models import (
    Availability,
    CompanyInfo,
    Compensation,
    EducationEntry,
    JobLocation,
    JobPosting,
    LocationPreference,
    UserProfile,
)


TECH_SKILLS = [
    "Python",
    "JavaScript",
    "SQL",
    "React",
    "TypeScript",
    "AWS",
    "Docker",
    "Kubernetes",
    "Machine Learning",
    "Data Analysis",
]

SOFT_SKILLS = [
    "communication",
    "leadership",
    "collaboration",
    "autonomy",
    "ownership",
    "customer-focus",
    "analytical-thinking",
    "adaptability",
]

ROLES = [
    "Data Engineer",
    "Software Engineer",
    "Machine Learning Engineer",
    "Product Manager",
    "DevOps Engineer",
]

INDUSTRIES = [
    "FinTech",
    "HealthTech",
    "E-Commerce",
    "AI",
    "Gaming",
]


@dataclass
class SyntheticDataset:
    users: List[UserProfile]
    jobs: List[JobPosting]


class DatasetFactory:
    """Generate deterministic synthetic data for unit tests."""

    def __init__(self, seed: int = 13) -> None:
        self.random = random.Random(seed)

    def random_skills(self, population: List[str], k: int) -> List[str]:
        return self.random.sample(population, k=k)

    def make_user(self, idx: int) -> UserProfile:
        hard_skills = self.random_skills(TECH_SKILLS, k=5)
        soft_skills = self.random_skills(SOFT_SKILLS, k=4)
        role = ROLES[idx % len(ROLES)]
        industry = INDUSTRIES[idx % len(INDUSTRIES)]
        availability = Availability(start_date=date.today(), notice_period_days=30)
        location_pref = LocationPreference(
            cities=["Amsterdam", "Berlin", "New York"],
            countries=["Netherlands", "Germany", "United States"],
            remote=True,
            hybrid=True,
            onsite=False,
            relocation=True,
        )
        return UserProfile(
            user_id=f"user-{idx}",
            hard_skills=hard_skills,
            soft_skills=soft_skills,
            years_experience=2 + idx % 10,
            roles_history=[role],
            industries_history=[industry],
            education=[EducationEntry(level="Bachelors", field="Computer Science", institution="Uni")],
            certifications=["AWS"],
            portfolio_links=["https://example.com"],
            desired_roles=[role],
            desired_industries=[industry],
            salary_min=60000,
            salary_max=110000,
            currency="USD",
            location_pref=location_pref,
            work_auth=["US"],
            availability=availability,
            career_goals="Grow into leadership while building scalable systems",
            constraints=["no_weekends"],
            preference_weights=None,
        )

    def make_job(self, idx: int) -> JobPosting:
        hard_skills = self.random_skills(TECH_SKILLS, k=5)
        soft_skills = self.random_skills(SOFT_SKILLS, k=3)
        role = ROLES[idx % len(ROLES)]
        industry = INDUSTRIES[idx % len(INDUSTRIES)]
        location = JobLocation(city="Amsterdam", country="Netherlands", remote=True, hybrid=True, onsite=False)
        compensation = Compensation(min=65000, max=105000, currency="USD", type="salary")
        posted_at = date.today() - timedelta(days=self.random.randint(0, 60))
        return JobPosting(
            job_id=f"job-{idx}",
            title=role,
            company=CompanyInfo(name=f"Company-{idx}", industry=industry),
            description="We are looking for passionate builders to join our team.",
            requirements=["Must have experience with modern tooling"],
            responsibilities=["Build systems", "Collaborate cross-functionally"],
            skills=hard_skills,
            seniority=self.random.choice(["junior", "mid", "senior"]),
            location=location,
            compensation=compensation,
            benefits=["healthcare", "stock options"],
            team_signals=["mentorship"],
            growth_opps=["manager_track", "IC_excellence"],
            company_culture=soft_skills,
            posted_at=posted_at,
        )

    def build(self, users: int = 20, jobs: int = 200) -> SyntheticDataset:
        return SyntheticDataset(
            users=[self.make_user(i) for i in range(users)],
            jobs=[self.make_job(j) for j in range(jobs)],
        )
