"""Rule-based matching: pick top candidate for a job after screening completes.

Edge case 3 (Phase 1): multiple job matches → notify HR of top 1.
Tested: tests/integration/test_edge_cases.py :: test_top_match_sent_to_hr
"""
from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Match


async def top_match_for_job(session: AsyncSession, job_id: uuid.UUID) -> Match | None:
    """Return the highest-scoring match for a job, or None."""
    stmt = (
        select(Match)
        .where(Match.job_id == job_id)
        .order_by(Match.score_total.desc(), Match.created_at.asc())
        .limit(1)
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def unnotified_top_matches(session: AsyncSession) -> list[Match]:
    """All matches where notified_hr=False, ranked best-first per job."""
    stmt = (
        select(Match)
        .where(Match.notified_hr.is_(False))
        .order_by(Match.job_id, Match.score_total.desc())
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())
