"""Job + content variant models."""
from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import Date, ForeignKey, Integer, Numeric, SmallInteger, Text, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    company_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    created_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("hr_users.id"), nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    salary_min_vnd: Mapped[int | None] = mapped_column(Integer)
    salary_max_vnd: Mapped[int | None] = mapped_column(Integer)
    salary_text: Mapped[str | None] = mapped_column(Text)
    location_raw: Mapped[str] = mapped_column(Text, nullable=False)
    location_district: Mapped[str] = mapped_column(Text, nullable=False)
    location_city: Mapped[str] = mapped_column(Text, nullable=False)
    location_lat: Mapped[Decimal] = mapped_column(Numeric(9, 6), nullable=False)
    location_lng: Mapped[Decimal] = mapped_column(Numeric(9, 6), nullable=False)
    start_date: Mapped[date | None] = mapped_column(Date)
    shift: Mapped[str | None] = mapped_column(Text)
    requirements_raw: Mapped[str | None] = mapped_column(Text)
    requirements_parsed: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    target_hires: Mapped[int] = mapped_column(Integer, server_default="1", nullable=False)
    status: Mapped[str] = mapped_column(Text, server_default="draft", nullable=False)
    ai_warnings: Mapped[list[dict[str, Any]] | None] = mapped_column(JSONB)
    # Override the company name shown on poster/post copy for this job.
    # Useful for agencies/freelance HR posting on behalf of multiple clients.
    company_name_override: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(server_default=text("now()"))
    published_at: Mapped[datetime | None] = mapped_column()
    closed_at: Mapped[datetime | None] = mapped_column()


class ContentVariant(Base):
    __tablename__ = "content_variants"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    job_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False)
    variant_index: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    hook_style: Mapped[str] = mapped_column(Text, nullable=False)
    copy_vietnamese: Mapped[str] = mapped_column(Text, nullable=False)
    final_copy: Mapped[str | None] = mapped_column(Text)
    generated_by_model: Mapped[str] = mapped_column(Text, nullable=False)
    token_usage: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    generated_at: Mapped[datetime] = mapped_column(server_default=text("now()"))
