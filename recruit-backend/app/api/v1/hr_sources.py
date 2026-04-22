"""HR-facing source management: list + create.

Extends tracking.py `POST /v1/hr/sources` with a GET list for the UI.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import db_session, require_hr_user
from app.db.models import HRUser, Source
from app.schemas.tracking import SourceResponse

router = APIRouter(prefix="/hr/sources", tags=["hr-sources"])


@router.get("", response_model=list[SourceResponse])
async def list_sources(
    db: AsyncSession = Depends(db_session),
    _hr: HRUser = Depends(require_hr_user),
) -> list[SourceResponse]:
    stmt = select(Source).order_by(Source.created_at.desc())
    rows = (await db.execute(stmt)).scalars().all()
    return [
        SourceResponse(
            id=s.id,
            channel=s.channel,  # type: ignore[arg-type]
            external_id=s.external_id,
            display_name=s.display_name,
        )
        for s in rows
    ]
