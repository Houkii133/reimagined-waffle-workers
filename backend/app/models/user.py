"""User and related models."""
from __future__ import annotations

from typing import Optional

from sqlalchemy import Column, JSON
from sqlmodel import Field

from .base import IDModel, TimestampMixin


class User(IDModel, TimestampMixin, table=True):
    __tablename__ = "users"

    email: str = Field(index=True, unique=True)
    hashed_password: str
    full_name: str | None = None
    is_active: bool = Field(default=True)
    is_admin: bool = Field(default=False)
    role: str = Field(default="candidate")

    # Relationships are managed via explicit queries to keep the model lightweight.
    # Refer to `UserProfile` and `Employer` tables using foreign keys.


class UserProfile(IDModel, TimestampMixin, table=True):
    __tablename__ = "user_profiles"

    user_id: int = Field(foreign_key="users.id", unique=True)
    bio: str | None = None
    skills: list = Field(default_factory=list, sa_column=Column(JSON, nullable=False, default=list))
    soft_skills: list = Field(default_factory=list, sa_column=Column(JSON, nullable=False, default=list))
    years_experience: int | None = None
    desired_roles: list = Field(default_factory=list, sa_column=Column(JSON, nullable=False, default=list))
    desired_industries: list = Field(default_factory=list, sa_column=Column(JSON, nullable=False, default=list))
    salary_currency: str = Field(default="USD")
    salary_min: int | None = None
    salary_max: int | None = None
    location_preferences: list = Field(default_factory=list, sa_column=Column(JSON, nullable=False, default=list))
    work_authorization: str | None = None
    career_goals: str | None = None
    resume_text: str | None = None

class Employer(IDModel, TimestampMixin, table=True):
    __tablename__ = "employers"

    user_id: int = Field(foreign_key="users.id")
    company_name: str
    company_size: str | None = None
    industry: str | None = None

    # Jobs are linked by the `jobs` table via employer_id.
