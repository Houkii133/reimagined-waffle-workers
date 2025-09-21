"""Job related models."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import Column, JSON
from sqlmodel import Field

from .base import IDModel, TimestampMixin


class Job(IDModel, TimestampMixin, table=True):
    __tablename__ = "jobs"

    employer_id: int = Field(foreign_key="employers.id")
    company_name: str
    title: str
    description: str
    location: str
    modality: str
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    salary_currency: str = Field(default="USD")
    industry: Optional[str] = None
    seniority: Optional[str] = None
    company_size: Optional[str] = None
    skills: list = Field(default_factory=list, sa_column=Column(JSON, nullable=False, default=list))
    responsibilities: list = Field(default_factory=list, sa_column=Column(JSON, nullable=False, default=list))
    requirements: list = Field(default_factory=list, sa_column=Column(JSON, nullable=False, default=list))
    culture_signals: list = Field(default_factory=list, sa_column=Column(JSON, nullable=False, default=list))
    growth_signals: list = Field(default_factory=list, sa_column=Column(JSON, nullable=False, default=list))
    is_active: bool = Field(default=True)
    posted_at: datetime = Field(default_factory=datetime.utcnow)



class FeedbackEvent(IDModel, TimestampMixin, table=True):
    __tablename__ = "feedback_events"

    user_id: int = Field(foreign_key="users.id")
    job_id: int = Field(foreign_key="jobs.id")
    event_type: str
    event_metadata: dict = Field(default_factory=dict, sa_column=Column(JSON, default=dict))
    engine_snapshot: Optional[dict] = Field(default=None, sa_column=Column(JSON, nullable=True))


class SavedJob(IDModel, TimestampMixin, table=True):
    __tablename__ = "saved_jobs"

    user_id: int = Field(foreign_key="users.id")
    job_id: int = Field(foreign_key="jobs.id")


class Application(IDModel, TimestampMixin, table=True):
    __tablename__ = "applications"

    user_id: int = Field(foreign_key="users.id")
    job_id: int = Field(foreign_key="jobs.id")
    status: str = Field(default="applied")
    notes: Optional[str] = None


class FeatureFlag(IDModel, TimestampMixin, table=True):
    __tablename__ = "feature_flags"

    key: str = Field(unique=True, index=True)
    enabled: bool = Field(default=True)
    payload: dict = Field(default_factory=dict, sa_column=Column(JSON, default=dict))
