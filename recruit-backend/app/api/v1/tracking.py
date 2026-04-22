"""Tracking / distribution endpoints."""
from __future__ import annotations

import hashlib
import logging
import uuid

from fastapi import APIRouter, Depends, Request, Response, status
from nanoid import generate as nanoid_generate
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import db_session, error_payload, get_request_id, require_hr_user
from app.db.models import ContentVariant, HRUser, Job, LinkClick, Source, TrackingLink
from app.schemas.tracking import (
    SourceCreateRequest,
    SourceResponse,
    TrackingLinkCreateRequest,
    TrackingLinkResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter(tags=["tracking"])


@router.post("/hr/sources", status_code=201, response_model=SourceResponse)
async def create_source(
    body: SourceCreateRequest,
    db: AsyncSession = Depends(db_session),
    hr: HRUser = Depends(require_hr_user),
) -> SourceResponse:
    source = Source(
        channel=body.channel,
        external_id=body.external_id,
        display_name=body.display_name,
        notes=body.notes,
    )
    db.add(source)
    await db.flush()
    await db.refresh(source)
    return SourceResponse(
        id=source.id,
        channel=source.channel,  # type: ignore[arg-type]
        external_id=source.external_id,
        display_name=source.display_name,
    )


@router.post(
    "/hr/jobs/{job_id}/tracking-links",
    status_code=201,
    response_model=TrackingLinkResponse,
)
async def create_tracking_link(
    job_id: uuid.UUID,
    body: TrackingLinkCreateRequest,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(db_session),
    hr: HRUser = Depends(require_hr_user),
    request_id: str = Depends(get_request_id),
) -> TrackingLinkResponse | dict:
    job = await db.get(Job, job_id)
    if job is None or job.company_id != hr.company_id:
        response.status_code = 404
        return error_payload("NOT_FOUND", "Không tìm thấy việc làm.", request_id)

    # Validate referenced entities
    variant = await db.get(ContentVariant, body.variant_id)
    if variant is None or variant.job_id != job.id:
        response.status_code = 400
        return error_payload(
            "VALIDATION_FAILED", "Biến thể không thuộc việc làm này.", request_id, field="variant_id"
        )
    source = await db.get(Source, body.source_id)
    if source is None:
        response.status_code = 400
        return error_payload(
            "VALIDATION_FAILED", "Nguồn không tồn tại.", request_id, field="source_id"
        )

    # Generate unique tracking_id
    for _ in range(3):
        tid = nanoid_generate(
            "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789", size=10
        )
        if await db.get(TrackingLink, tid) is None:
            break
    else:
        response.status_code = 500
        return error_payload("INTERNAL_ERROR", "Không tạo được mã.", request_id)

    link = TrackingLink(
        tracking_id=tid,
        job_id=job.id,
        variant_id=body.variant_id,
        source_id=body.source_id,
        campaign_id=body.campaign_id,
        created_by=hr.id,
    )
    db.add(link)
    await db.flush()
    base = str(request.base_url).rstrip("/")
    return TrackingLinkResponse(
        tracking_id=tid,
        share_url=f"{base}/j/{tid}",
        job_id=job.id,
        variant_id=body.variant_id,
        source_id=body.source_id,
    )


@router.get("/j/{tracking_id}")
async def public_landing(
    tracking_id: str,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(db_session),
    request_id: str = Depends(get_request_id),
) -> dict:
    """Public landing resolver. Logs click to link_clicks (trigger bumps counter).

    Returns a JSON body the frontend SSR can render. Frontend will embed tracking_id
    in the subsequent POST /leads call for attribution.
    """
    tlink = await db.get(TrackingLink, tracking_id)
    if tlink is None:
        response.status_code = 404
        return error_payload(
            "NOT_FOUND", "Việc làm không còn tuyển. Xem việc khác tại v.vn.", request_id
        )
    job = await db.get(Job, tlink.job_id)
    variant = await db.get(ContentVariant, tlink.variant_id)
    if job is None or job.status != "active" or variant is None:
        response.status_code = 404
        return error_payload(
            "NOT_FOUND", "Việc làm không còn tuyển.", request_id
        )

    # Log click
    ip = request.client.host if request.client else ""
    ip_hash = hashlib.sha256(f"{ip}|{tracking_id}".encode()).hexdigest()[:32] if ip else None
    click = LinkClick(
        tracking_id=tracking_id,
        ip_hash=ip_hash,
        user_agent=request.headers.get("user-agent"),
        referrer=request.headers.get("referer"),
    )
    db.add(click)
    await db.flush()

    return {
        "tracking_id": tracking_id,
        "title": job.title,
        "salary_text": job.salary_text,
        "location_short": f"{job.location_district}, {job.location_city}",
        "start_date": job.start_date.isoformat() if job.start_date else None,
        "copy_vietnamese": variant.final_copy or variant.copy_vietnamese,
        "apply_cta": "ĐĂNG KÝ 30 GIÂY",
    }
