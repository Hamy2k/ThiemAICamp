"""HR-facing jobs list endpoint (fills Phase 1 gap)."""
from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Literal

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import db_session, require_hr_user
from app.db.models import HRUser, Job, Lead, Match, TrackingLink

router = APIRouter(prefix="/hr/jobs", tags=["hr-jobs-list"])


class JobListItem(BaseModel):
    id: uuid.UUID
    title: str
    status: Literal["draft", "active", "paused", "closed"]
    location_short: str
    salary_text: str | None
    target_hires: int
    created_at: datetime
    lead_count: int
    qualified_count: int
    total_clicks: int


class JobListResponse(BaseModel):
    items: list[JobListItem]
    total: int


@router.get("/list", response_model=JobListResponse)
async def list_jobs(
    status: str | None = Query(default=None, regex="^(draft|active|paused|closed)$"),
    limit: int = Query(default=50, ge=1, le=200),
    db: AsyncSession = Depends(db_session),
    hr: HRUser = Depends(require_hr_user),
) -> JobListResponse:
    """List jobs for this HR's company with lead + click counters."""
    stmt = (
        select(Job)
        .where(Job.company_id == hr.company_id)
        .order_by(Job.created_at.desc())
        .limit(limit)
    )
    if status:
        stmt = stmt.where(Job.status == status)
    jobs = (await db.execute(stmt)).scalars().all()

    items: list[JobListItem] = []
    for j in jobs:
        leads_q = await db.execute(
            select(func.count(Lead.id))
            .where(Lead.entry_job_id == j.id, Lead.is_duplicate_of.is_(None))
        )
        lead_count = int(leads_q.scalar() or 0)

        qual_q = await db.execute(
            select(func.count(Match.id))
            .where(Match.job_id == j.id, Match.tier.in_(["hot", "warm"]))
        )
        qualified = int(qual_q.scalar() or 0)

        clicks_q = await db.execute(
            select(func.coalesce(func.sum(TrackingLink.click_count), 0))
            .where(TrackingLink.job_id == j.id)
        )
        clicks = int(clicks_q.scalar() or 0)

        items.append(
            JobListItem(
                id=j.id,
                title=j.title,
                status=j.status,  # type: ignore[arg-type]
                location_short=f"{j.location_district}, {j.location_city}",
                salary_text=j.salary_text,
                target_hires=j.target_hires,
                created_at=j.created_at,
                lead_count=lead_count,
                qualified_count=qualified,
                total_clicks=clicks,
            )
        )
    return JobListResponse(items=items, total=len(items))
