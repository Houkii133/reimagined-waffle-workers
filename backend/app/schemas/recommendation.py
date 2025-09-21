"""Recommendation schemas."""
from __future__ import annotations

from typing import Any, Dict, List

from pydantic import BaseModel


class MatchRecommendation(BaseModel):
    job_id: int
    score: float
    rationale: List[str]
    fit_dimensions: Dict[str, float]
    qualification_gaps: List[str]


class RecommendationList(BaseModel):
    items: List[MatchRecommendation]


class FeedbackRequest(BaseModel):
    job_id: int
    event_type: str
    metadata: Dict[str, Any] | None = None


class WhyNotResponse(BaseModel):
    job_id: int
    missing_skills: List[str]
    message: str


class WhatIfRequest(BaseModel):
    changes: Dict[str, Any]


class WhatIfResponse(BaseModel):
    items: List[MatchRecommendation]
