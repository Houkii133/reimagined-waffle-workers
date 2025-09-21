"""Typed data models for the job matching engine."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Dict, List, Optional


@dataclass(frozen=True)
class EducationEntry:
    """Represents an education credential."""

    level: str
    field: str
    institution: str


@dataclass(frozen=True)
class Availability:
    """Represents candidate availability."""

    start_date: Optional[date]
    notice_period_days: Optional[int]


@dataclass(frozen=True)
class LocationPreference:
    """Represents user location preferences."""

    cities: List[str] = field(default_factory=list)
    countries: List[str] = field(default_factory=list)
    remote: bool = True
    hybrid: bool = True
    onsite: bool = True
    relocation: bool = False


@dataclass(frozen=True)
class UserProfile:
    """Structured representation of a job seeker."""

    user_id: str
    hard_skills: List[str]
    soft_skills: List[str]
    years_experience: float
    roles_history: List[str]
    industries_history: List[str]
    education: List[EducationEntry]
    certifications: List[str]
    portfolio_links: List[str]
    desired_roles: List[str]
    desired_industries: List[str]
    salary_min: int
    salary_max: int
    currency: str
    location_pref: LocationPreference
    work_auth: List[str]
    availability: Availability
    career_goals: str
    constraints: List[str]
    preference_weights: Optional[Dict[str, float]] = None


@dataclass(frozen=True)
class CompanyInfo:
    """Represents company metadata."""

    name: str
    size: Optional[str] = None
    industry: Optional[str] = None
    stage: Optional[str] = None


@dataclass(frozen=True)
class JobLocation:
    """Represents a job's location configuration."""

    city: Optional[str] = None
    country: Optional[str] = None
    remote: Optional[bool] = None
    hybrid: Optional[bool] = None
    onsite: Optional[bool] = None
    visa: Optional[str] = None


@dataclass(frozen=True)
class Compensation:
    """Represents compensation information."""

    min: Optional[int] = None
    max: Optional[int] = None
    currency: Optional[str] = None
    type: Optional[str] = None  # salary | hourly


@dataclass(frozen=True)
class JobPosting:
    """Structured job posting."""

    job_id: str
    title: str
    company: CompanyInfo
    description: str
    requirements: List[str]
    responsibilities: List[str]
    skills: List[str]
    seniority: str
    location: JobLocation
    compensation: Optional[Compensation] = None
    benefits: List[str] = field(default_factory=list)
    team_signals: List[str] = field(default_factory=list)
    growth_opps: List[str] = field(default_factory=list)
    company_culture: List[str] = field(default_factory=list)
    posted_at: Optional[date] = None


@dataclass
class MatchRecommendation:
    """Recommendation output for a user and job pair."""

    job_id: str
    score: float
    rank: int
    rationale: List[str]
    qualification_gaps: List[str]
    fit_dimensions: Dict[str, float]
    confidence: float


@dataclass(frozen=True)
class Feedback:
    """Feedback signal from a user."""

    user_id: str
    job_id: str
    signal_type: str
    value: Optional[float]
    timestamp: datetime
    free_text: Optional[str] = None


@dataclass
class WhyNotExplanation:
    """Represents reasons why a job was filtered out."""

    job_id: str
    blocked: bool
    reasons: List[str]


@dataclass
class Telemetry:
    """Telemetry counters for governance and audits."""

    filtered_counts: Dict[str, int] = field(default_factory=dict)
    bias_metrics: Dict[str, float] = field(default_factory=dict)

    def increment(self, key: str) -> None:
        self.filtered_counts[key] = self.filtered_counts.get(key, 0) + 1


@dataclass
class DebugTrace:
    """Captures debug information for transparency."""

    seed: int
    features: Dict[str, float]
    scores: Dict[str, float]
    weights: Dict[str, float]
    rationale: List[str]


PreferenceWeights = Dict[str, float]
FitDimensions = Dict[str, float]
