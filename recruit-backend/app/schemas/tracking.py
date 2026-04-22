"""Tracking + attribution schemas."""
from __future__ import annotations

import uuid
from typing import Literal

from pydantic import BaseModel, Field


ChannelLiteral = Literal["facebook", "zalo", "direct", "unknown", "other"]


class SourceCreateRequest(BaseModel):
    channel: ChannelLiteral
    external_id: str | None = Field(default=None, max_length=200)
    display_name: str = Field(min_length=2, max_length=200)
    notes: str | None = None


class SourceResponse(BaseModel):
    id: uuid.UUID
    channel: ChannelLiteral
    external_id: str | None
    display_name: str


class TrackingLinkCreateRequest(BaseModel):
    variant_id: uuid.UUID
    source_id: uuid.UUID
    campaign_id: uuid.UUID | None = None


class TrackingLinkResponse(BaseModel):
    tracking_id: str
    share_url: str
    job_id: uuid.UUID
    variant_id: uuid.UUID
    source_id: uuid.UUID
