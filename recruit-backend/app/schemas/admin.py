"""Admin (HR-side) schemas — listing + detail for leads."""
from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict


Tier = Literal["hot", "warm", "cold"]


class LeadListItem(BaseModel):
    """One row in the admin leads list."""
    model_config = ConfigDict(from_attributes=True)
    lead_id: uuid.UUID
    match_id: uuid.UUID | None
    session_id: uuid.UUID | None
    full_name: str
    phone_masked: str
    area: str | None
    score_total: Decimal | None
    tier: Tier | None
    distance_km: Decimal | None
    job_id: uuid.UUID | None
    job_title: str | None
    source_display_name: str | None
    created_at: datetime
    session_status: Literal["in_progress", "completed", "abandoned"] | None


class LeadListResponse(BaseModel):
    items: list[LeadListItem]
    total: int


class TranscriptMessage(BaseModel):
    turn_index: int
    role: Literal["user", "assistant", "system"]
    content: str
    created_at: datetime


class ScoreBreakdown(BaseModel):
    location: Decimal
    availability: Decimal
    experience: Decimal
    response_quality: Decimal


class LeadAttribution(BaseModel):
    source_channel: str
    source_display_name: str | None
    tracking_id: str | None
    variant_hook_style: str | None


class LeadDetailResponse(BaseModel):
    lead_id: uuid.UUID
    full_name: str
    phone_masked: str
    phone_full: str  # HR sees real phone (they need to call)
    area_normalized: str | None
    area_raw: str | None
    created_at: datetime

    # Match info (may be null if lead didn't complete screening)
    match_id: uuid.UUID | None
    score_total: Decimal | None
    tier: Tier | None
    score_breakdown: ScoreBreakdown | None
    distance_km: Decimal | None
    explanation_vi: str | None

    # Job + attribution
    job_id: uuid.UUID | None
    job_title: str | None
    attribution: LeadAttribution | None

    # Session
    session_id: uuid.UUID | None
    session_status: Literal["in_progress", "completed", "abandoned"] | None
    turn_count: int | None
    extracted_data: dict[str, Any] | None
    transcript: list[TranscriptMessage]

    # Consent
    consent_version: str | None
    consent_granted_at: datetime | None
