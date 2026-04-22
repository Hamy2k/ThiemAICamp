"""Lead + consent models."""
from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import ForeignKey, Numeric, Text, text
from sqlalchemy.dialects.postgresql import INET, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Lead(Base):
    __tablename__ = "leads"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    phone_e164: Mapped[str] = mapped_column(Text, nullable=False)  # PII
    phone_raw: Mapped[str] = mapped_column(Text, nullable=False)   # PII
    full_name: Mapped[str] = mapped_column(Text, nullable=False)   # PII
    area_raw: Mapped[str | None] = mapped_column(Text)             # PII
    area_normalized: Mapped[str | None] = mapped_column(Text)
    area_district: Mapped[str | None] = mapped_column(Text)
    area_city: Mapped[str | None] = mapped_column(Text)
    area_lat: Mapped[Decimal | None] = mapped_column(Numeric(9, 6))
    area_lng: Mapped[Decimal | None] = mapped_column(Numeric(9, 6))
    source_channel: Mapped[str] = mapped_column(Text, server_default="unknown", nullable=False)
    source_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("sources.id"))
    variant_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("content_variants.id"))
    tracking_id: Mapped[str | None] = mapped_column(Text, ForeignKey("tracking_links.tracking_id"))
    campaign_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("campaigns.id"))
    entry_job_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("jobs.id"))
    user_agent: Mapped[str | None] = mapped_column(Text)
    ip_address: Mapped[str | None] = mapped_column(INET)  # PII
    is_duplicate_of: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("leads.id"))
    consent_record_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    created_at: Mapped[datetime] = mapped_column(server_default=text("now()"))
    last_active_at: Mapped[datetime] = mapped_column(server_default=text("now()"))


class ConsentRecord(Base):
    __tablename__ = "consent_records"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    lead_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("leads.id", ondelete="RESTRICT"), nullable=False)
    consent_version: Mapped[str] = mapped_column(Text, nullable=False)
    consent_text_vi: Mapped[str] = mapped_column(Text, nullable=False)
    purposes: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    granted_at: Mapped[datetime] = mapped_column(nullable=False)
    ip_address: Mapped[str | None] = mapped_column(INET)  # PII
    user_agent: Mapped[str | None] = mapped_column(Text)
    revoked_at: Mapped[datetime | None] = mapped_column()
