"""Match model (scored + ranked candidates)."""
from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, ForeignKey, Integer, Numeric, Text, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Match(Base):
    __tablename__ = "matches"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    lead_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("leads.id", ondelete="CASCADE"), nullable=False)
    job_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False)
    session_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("screening_sessions.id"))
    score_total: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    score_location: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    score_availability: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    score_experience: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    score_response_quality: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    explanation_vi: Mapped[str] = mapped_column(Text, nullable=False)
    tier: Mapped[str] = mapped_column(Text, nullable=False)
    distance_km: Mapped[Decimal | None] = mapped_column(Numeric(6, 2))
    rank_for_job: Mapped[int | None] = mapped_column(Integer)
    notified_hr: Mapped[bool] = mapped_column(Boolean, server_default="false", nullable=False)
    notified_at: Mapped[datetime | None] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(server_default=text("now()"))
