"""Job-related request/response schemas."""
from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


ShiftLiteral = Literal["day", "night", "rotating", "flexible"]
JobStatus = Literal["draft", "active", "paused", "closed"]
HookStyle = Literal["urgency", "salary_first", "proximity", "friendly", "detailed"]


class JobCreateRequest(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    salary_text: str | None = None
    location_raw: str = Field(min_length=3, max_length=500)
    requirements_raw: str | None = None
    shift: ShiftLiteral | None = None
    start_date: date | None = None
    target_hires: int = Field(default=1, ge=1, le=500)


class AIWarning(BaseModel):
    code: Literal["SALARY_BELOW_MARKET", "VAGUE_LOCATION", "UNREALISTIC_REQUIREMENT"]
    message: str


class JobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    status: JobStatus
    title: str
    salary_min_vnd: int | None
    salary_max_vnd: int | None
    salary_text: str | None
    location_district: str
    location_city: str
    location_lat: Decimal
    location_lng: Decimal
    start_date: date | None
    shift: ShiftLiteral | None
    requirements_parsed: dict[str, Any] | None
    ai_warnings: list[AIWarning] | None
    created_at: datetime


class JobPatchRequest(BaseModel):
    status: JobStatus | None = None
    final_copy: str | None = None


class ContentVariantResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    variant_index: int
    hook_style: HookStyle
    copy_vietnamese: str
    final_copy: str | None = None


class ShareKitItem(BaseModel):
    """One ready-to-post card: variant text + tracking link + poster image."""
    source_id: uuid.UUID
    source_display_name: str
    source_channel: str
    variant_id: uuid.UUID
    tracking_id: str
    copy_with_placeholder: str  # Still has `{link}` — frontend substitutes with its own origin.
    poster_url: str | None = None  # Path under backend origin, e.g. /posters/<job_id>.png


class GenerateContentResponse(BaseModel):
    variants: list[ContentVariantResponse]
    warnings: list[AIWarning]
    token_usage: dict[str, Any]
    share_kit: list[ShareKitItem]
