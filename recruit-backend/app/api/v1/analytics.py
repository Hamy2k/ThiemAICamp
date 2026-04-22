"""HR analytics endpoints (sources / variants)."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import db_session, require_hr_user
from app.db.models import ContentVariant, HRUser, Match, Source, TrackingLink
from app.schemas.match import SourceAnalyticsRow, VariantAnalyticsRow

router = APIRouter(prefix="/hr/analytics", tags=["hr-analytics"])


@router.get("/sources")
async def sources_report(
    job_id: uuid.UUID = Query(...),
    db: AsyncSession = Depends(db_session),
    _hr: HRUser = Depends(require_hr_user),
) -> dict:
    stmt = text("""
        SELECT
          s.channel AS source_channel,
          s.id      AS source_id,
          s.display_name,
          COALESCE(SUM(tl.click_count), 0)::int AS clicks,
          COALESCE(SUM(tl.lead_count), 0)::int  AS leads,
          COALESCE(COUNT(m.id) FILTER (WHERE m.tier IN ('hot','warm')), 0)::int AS qualified
        FROM sources s
        JOIN tracking_links tl ON tl.source_id = s.id
        LEFT JOIN leads l      ON l.tracking_id = tl.tracking_id
        LEFT JOIN matches m    ON m.lead_id = l.id
        WHERE tl.job_id = :job_id
        GROUP BY s.id, s.channel, s.display_name
        ORDER BY leads DESC
    """)
    rows = (await db.execute(stmt, {"job_id": str(job_id)})).mappings().all()
    out = []
    for r in rows:
        clicks, leads = r["clicks"], r["leads"]
        ctr = (100.0 * leads / clicks) if clicks else None
        conv = ctr  # leads/clicks is our conversion here
        out.append(SourceAnalyticsRow(
            source_channel=r["source_channel"],
            source_id=r["source_id"],
            display_name=r["display_name"],
            clicks=clicks,
            leads=leads,
            qualified=r["qualified"],
            ctr_pct=round(ctr, 2) if ctr is not None else None,
            conversion_pct=round(conv, 2) if conv is not None else None,
        ).model_dump())
    return {"rows": out}


@router.get("/variants")
async def variants_report(
    job_id: uuid.UUID = Query(...),
    db: AsyncSession = Depends(db_session),
    _hr: HRUser = Depends(require_hr_user),
) -> dict:
    stmt = text("""
        SELECT
          v.id           AS variant_id,
          v.variant_index,
          v.hook_style,
          COALESCE(SUM(tl.click_count), 0)::int AS clicks,
          COALESCE(SUM(tl.lead_count), 0)::int  AS leads,
          COALESCE(COUNT(m.id) FILTER (WHERE m.tier IN ('hot','warm')), 0)::int AS qualified
        FROM content_variants v
        LEFT JOIN tracking_links tl ON tl.variant_id = v.id
        LEFT JOIN leads l           ON l.tracking_id = tl.tracking_id
        LEFT JOIN matches m         ON m.lead_id = l.id
        WHERE v.job_id = :job_id
        GROUP BY v.id, v.variant_index, v.hook_style
        ORDER BY qualified DESC, leads DESC
    """)
    rows = (await db.execute(stmt, {"job_id": str(job_id)})).mappings().all()
    out = []
    for r in rows:
        clicks, leads = r["clicks"], r["leads"]
        conv = (100.0 * leads / clicks) if clicks else None
        out.append(VariantAnalyticsRow(
            variant_id=r["variant_id"],
            variant_index=r["variant_index"],
            hook_style=r["hook_style"],
            clicks=clicks,
            leads=leads,
            qualified=r["qualified"],
            conversion_pct=round(conv, 2) if conv is not None else None,
        ).model_dump())
    return {"rows": out}
