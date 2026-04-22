"""Lead + consent schemas."""
from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class ConsentInput(BaseModel):
    version: str
    accepted: bool


class LeadCreateRequest(BaseModel):
    tracking_id: str | None = Field(default=None, max_length=20)
    full_name: str = Field(min_length=1, max_length=200)
    phone: str = Field(min_length=8, max_length=30)
    area_raw: str | None = Field(default=None, max_length=200)
    consent: ConsentInput


class NormalizedLeadInfo(BaseModel):
    phone_e164: str
    area_normalized: str | None
    distance_km: float | None


class LeadCreateResponse(BaseModel):
    lead_id: uuid.UUID
    session_id: uuid.UUID
    normalized: NormalizedLeadInfo
    first_ai_message: str


class LeadDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    phone_e164: str
    full_name: str
    area_normalized: str | None
    area_district: str | None
    area_city: str | None
    source_channel: str
    tracking_id: str | None
    created_at: datetime


class DeletionResponse(BaseModel):
    deleted: bool
    deleted_at: datetime
