"""Match / analytics schemas."""
from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel


class LeadSummary(BaseModel):
    name: str
    phone_masked: str
    area: str | None
    distance_km: Decimal | None


class MatchItem(BaseModel):
    match_id: uuid.UUID
    score_total: Decimal
    tier: Literal["hot", "warm", "cold"]
    lead: LeadSummary
    explanation_vi: str
    created_at: datetime


class SourceAnalyticsRow(BaseModel):
    source_channel: str
    source_id: uuid.UUID | None
    display_name: str
    clicks: int
    leads: int
    qualified: int
    ctr_pct: float | None
    conversion_pct: float | None


class VariantAnalyticsRow(BaseModel):
    variant_id: uuid.UUID
    variant_index: int
    hook_style: str
    clicks: int
    leads: int
    qualified: int
    conversion_pct: float | None
