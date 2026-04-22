"""Screening chat schemas.

Applies validation patches:
- P3: extracted_delta includes hours_per_day + prefers_proximity
- P4: start_date accepts ISO | 'asap' | 'next_week' | 'next_month'
"""
from __future__ import annotations

import uuid
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


ShiftPreference = Literal["day", "night", "rotating", "any"]


class ShiftAvailability(BaseModel):
    day: bool | None = None
    night: bool | None = None
    rotating: bool | None = None
    preferred: ShiftPreference | None = None


class ExperienceInfo(BaseModel):
    has_experience: bool | None = None
    years: float | None = None
    related_keywords: list[str] = Field(default_factory=list)
    willing_to_learn: bool | None = None


class ExtractedDelta(BaseModel):
    """Delta of what was learned in this turn — merged into session.extracted_data."""
    model_config = ConfigDict(extra="ignore")

    start_date: str | None = Field(
        default=None,
        description="ISO date | 'asap' | 'next_week' | 'next_month'",
    )
    shift_availability: ShiftAvailability | None = None
    experience: ExperienceInfo | None = None
    questions_from_candidate: list[str] = Field(default_factory=list)
    normalized_location: dict[str, str] | None = None
    # Validation patch P3: extended fields
    hours_per_day: float | None = Field(default=None, ge=1, le=24)
    prefers_proximity: bool | None = None


class ScreeningTurnRequest(BaseModel):
    session_id: uuid.UUID
    message: str = Field(min_length=1, max_length=1000)


class ScreeningTurnResponse(BaseModel):
    turn_index: int
    reply: str
    extracted_delta: ExtractedDelta
    turns_remaining: int
    done: bool


class ScreeningCompleteRequest(BaseModel):
    session_id: uuid.UUID


class ScoreBreakdown(BaseModel):
    location: Decimal
    availability: Decimal
    experience: Decimal
    response_quality: Decimal


class ScreeningCompleteResponse(BaseModel):
    match_id: uuid.UUID
    score_total: Decimal
    score_breakdown: ScoreBreakdown
    tier: Literal["hot", "warm", "cold"]
    explanation_vi: str
    thank_you_message: str
    fallback_used: bool = False
