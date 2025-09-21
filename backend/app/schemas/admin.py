"""Admin schemas."""
from __future__ import annotations

from typing import Any, Dict

from pydantic import BaseModel


class TelemetryResponse(BaseModel):
    jobs_indexed: int
    feedback_events: int


class FeatureFlagUpdate(BaseModel):
    key: str
    enabled: bool
    payload: Dict[str, Any] | None = None
