"""HR-facing leads endpoints: list + detail.

Fills Phase 1 gap flagged by Phase 3 (GET /v1/hr/leads + GET /v1/hr/leads/:id).
"""
from __future__ import annotations

import logging
import uuid
from decimal import Decimal

from fastapi import APIRouter, Depends, Query, Response
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import db_session, error_payload, get_request_id, require_hr_user
from app.db.models import (
    ConsentRecord,
    ContentVariant,
    HRUser,
    Job,
    Lead,
    Match,
    ScreeningMessage,
    ScreeningSession,
    Source,
    TrackingLink,
)
from app.schemas.admin import (
    LeadAttribution,
    LeadDetailResponse,
    LeadListItem,
    LeadListResponse,
    ScoreBreakdown,
    TranscriptMessage,
)
from app.utils.phone import mask_phone

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/hr/leads", tags=["hr-leads"])


@router.get("", response_model=LeadListResponse)
async def list_leads(
    job_id: uuid.UUID | None = Query(default=None),
    tier: str | None = Query(default=None, regex="^(hot|warm|cold)$"),
    limit: int = Query(default=50, ge=1, le=200),
    db: AsyncSession = Depends(db_session),
    hr: HRUser = Depends(require_hr_user),
) -> LeadListResponse:
    """List leads for the HR's company, newest first.

    Includes both completed (has match) and in-progress leads. Uses LEFT JOIN
    so leads without matches still appear — HR can see abandoned sessions.
    """
    # Build query via SQLAlchemy ORM with joins + optional filters
    stmt = (
        select(
            Lead,
            Match,
            ScreeningSession,
            Job,
            Source,
        )
        .outerjoin(Match, Match.lead_id == Lead.id)
        .outerjoin(ScreeningSession, ScreeningSession.id == Match.session_id)
        .outerjoin(Job, Job.id == Match.job_id)
        .outerjoin(Source, Source.id == Lead.source_id)
        .where(
            Lead.is_duplicate_of.is_(None),
            (Job.company_id == hr.company_id) | (Lead.entry_job_id.is_not(None)),
        )
        .order_by(Lead.created_at.desc())
        .limit(limit)
    )
    if job_id is not None:
        stmt = stmt.where(Match.job_id == job_id)
    if tier is not None:
        stmt = stmt.where(Match.tier == tier)

    rows = (await db.execute(stmt)).all()

    # Fallback — if a lead never got a match (abandoned), grab session directly
    items: list[LeadListItem] = []
    for lead, match, session, job, source in rows:
        items.append(
            LeadListItem(
                lead_id=lead.id,
                match_id=match.id if match else None,
                session_id=session.id if session else None,
                full_name=lead.full_name,
                phone_masked=mask_phone(lead.phone_e164),
                area=lead.area_normalized,
                score_total=match.score_total if match else None,
                tier=match.tier if match else None,  # type: ignore[arg-type]
                distance_km=match.distance_km if match else None,
                job_id=job.id if job else lead.entry_job_id,
                job_title=job.title if job else None,
                source_display_name=source.display_name if source else None,
                created_at=lead.created_at,
                session_status=session.status if session else None,  # type: ignore[arg-type]
            )
        )

    return LeadListResponse(items=items, total=len(items))


@router.get("/{lead_id}", response_model=LeadDetailResponse)
async def lead_detail(
    lead_id: uuid.UUID,
    response: Response,
    db: AsyncSession = Depends(db_session),
    hr: HRUser = Depends(require_hr_user),
    request_id: str = Depends(get_request_id),
) -> LeadDetailResponse | dict:
    """Full detail for one lead: match + session + transcript + attribution + consent."""
    lead = await db.get(Lead, lead_id)
    if lead is None:
        return JSONResponse(
            status_code=404,
            content=error_payload("NOT_FOUND", "Không tìm thấy ứng viên.", request_id),
        )

    # Match (may be None if not completed screening)
    match = (await db.execute(select(Match).where(Match.lead_id == lead_id).limit(1))).scalar_one_or_none()

    # Session
    session = (
        await db.execute(select(ScreeningSession).where(ScreeningSession.lead_id == lead_id).limit(1))
    ).scalar_one_or_none()

    # Transcript
    transcript: list[TranscriptMessage] = []
    if session is not None:
        msg_stmt = (
            select(ScreeningMessage)
            .where(ScreeningMessage.session_id == session.id)
            .order_by(ScreeningMessage.turn_index, ScreeningMessage.id)
        )
        for m in (await db.execute(msg_stmt)).scalars().all():
            transcript.append(
                TranscriptMessage(
                    turn_index=m.turn_index,
                    role=m.role,  # type: ignore[arg-type]
                    content=m.content,
                    created_at=m.created_at,
                )
            )

    # Job
    job_id = match.job_id if match else lead.entry_job_id
    job = await db.get(Job, job_id) if job_id else None
    # Authorization: only show leads whose job belongs to this HR's company.
    # If no job link at all, still allow (orphan lead — edge case).
    if job and job.company_id != hr.company_id:
        return JSONResponse(
            status_code=403,
            content=error_payload("FORBIDDEN", "Ứng viên thuộc công ty khác.", request_id),
        )

    # Attribution
    attribution: LeadAttribution | None = None
    if lead.tracking_id:
        tlink = await db.get(TrackingLink, lead.tracking_id)
        src = await db.get(Source, lead.source_id) if lead.source_id else None
        variant = await db.get(ContentVariant, tlink.variant_id) if tlink else None
        attribution = LeadAttribution(
            source_channel=lead.source_channel,
            source_display_name=src.display_name if src else None,
            tracking_id=lead.tracking_id,
            variant_hook_style=variant.hook_style if variant else None,
        )
    else:
        attribution = LeadAttribution(
            source_channel=lead.source_channel,
            source_display_name=None,
            tracking_id=None,
            variant_hook_style=None,
        )

    # Consent
    consent = None
    if lead.consent_record_id:
        consent = await db.get(ConsentRecord, lead.consent_record_id)

    breakdown: ScoreBreakdown | None = None
    if match is not None:
        breakdown = ScoreBreakdown(
            location=match.score_location,
            availability=match.score_availability,
            experience=match.score_experience,
            response_quality=match.score_response_quality,
        )

    return LeadDetailResponse(
        lead_id=lead.id,
        full_name=lead.full_name,
        phone_masked=mask_phone(lead.phone_e164),
        phone_full=lead.phone_e164,
        area_normalized=lead.area_normalized,
        area_raw=lead.area_raw,
        created_at=lead.created_at,
        match_id=match.id if match else None,
        score_total=match.score_total if match else None,
        tier=match.tier if match else None,  # type: ignore[arg-type]
        score_breakdown=breakdown,
        distance_km=match.distance_km if match else None,
        explanation_vi=match.explanation_vi if match else None,
        job_id=job.id if job else None,
        job_title=job.title if job else None,
        attribution=attribution,
        session_id=session.id if session else None,
        session_status=session.status if session else None,  # type: ignore[arg-type]
        turn_count=session.turn_count if session else None,
        extracted_data=session.extracted_data if session else None,
        transcript=transcript,
        consent_version=consent.consent_version if consent else None,
        consent_granted_at=consent.granted_at if consent else None,
    )
