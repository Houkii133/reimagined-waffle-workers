"""Job schemas."""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class JobBase(BaseModel):
    title: str
    description: str
    location: str
    modality: str
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    salary_currency: str = "USD"
    industry: Optional[str] = None
    seniority: Optional[str] = None
    company_size: Optional[str] = None
    skills: List[str] = Field(default_factory=list)
    responsibilities: List[str] = Field(default_factory=list)
    requirements: List[str] = Field(default_factory=list)
    culture_signals: List[str] = Field(default_factory=list)
    growth_signals: List[str] = Field(default_factory=list)
    is_active: bool = True


class JobCreate(JobBase):
    pass


class JobUpdate(JobBase):
    pass


class JobRead(JobBase):
    id: int
    employer_id: int
    company_name: str
    posted_at: datetime
    created_at: datetime
    updated_at: datetime


class JobListResponse(BaseModel):
    total: int
    items: List[JobRead]
