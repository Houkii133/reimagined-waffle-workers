"""User schemas."""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field


class UserProfileBase(BaseModel):
    bio: Optional[str] = None
    skills: List[str] = Field(default_factory=list)
    soft_skills: List[str] = Field(default_factory=list)
    years_experience: Optional[int] = None
    desired_roles: List[str] = Field(default_factory=list)
    desired_industries: List[str] = Field(default_factory=list)
    salary_currency: str = "USD"
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    location_preferences: List[str] = Field(default_factory=list)
    work_authorization: Optional[str] = None
    career_goals: Optional[str] = None
    resume_text: Optional[str] = None


class UserProfileCreate(UserProfileBase):
    pass


class UserProfileRead(UserProfileBase):
    id: int
    created_at: datetime
    updated_at: datetime


class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    role: str = "candidate"


class UserRead(UserBase):
    id: int
    is_active: bool
    is_admin: bool
    created_at: datetime
    updated_at: datetime
    profile: Optional[UserProfileRead] = None


class UserUpdate(UserProfileBase):
    full_name: Optional[str] = None
