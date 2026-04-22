"""HR job management endpoints."""
from __future__ import annotations

import logging
import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.client import ClaudeUnavailableError
from app.ai.job_generator import generate_variants
from app.api.deps import db_session, error_payload, get_request_id, require_hr_user
from app.db.models import Company, ContentVariant, HRUser, Job, Source, TrackingLink
from app.schemas.job import (
    AIWarning,
    ContentVariantResponse,
    GenerateContentResponse,
    JobCreateRequest,
    JobPatchRequest,
    JobResponse,
    ShareKitItem,
)
from nanoid import generate as nanoid_generate
from app.services.gazetteer import search_by_fuzzy_name
from app.services.poster import generate_poster

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/hr/jobs", tags=["hr-jobs"])


def _parse_salary(text: str | None) -> tuple[int | None, int | None]:
    """Parse '8-10 triệu' / '8.5 triệu' etc into (min, max) VND."""
    if not text:
        return None, None
    import re
    nums = re.findall(r"(\d+(?:[.,]\d+)?)", text)
    if not nums:
        return None, None
    vals = [int(float(n.replace(",", ".")) * 1_000_000) for n in nums[:2]]
    if len(vals) == 1:
        return vals[0], vals[0]
    return min(vals), max(vals)


@router.post("", status_code=status.HTTP_201_CREATED, response_model=JobResponse)
async def create_job(
    body: JobCreateRequest,
    response: Response,
    db: AsyncSession = Depends(db_session),
    hr: HRUser = Depends(require_hr_user),
    request_id: str = Depends(get_request_id),
) -> JobResponse | dict:
    """Create a draft job (edge case 4 — unrealistic salary tracked via ai_warnings later)."""
    resolved = search_by_fuzzy_name(body.location_raw)
    if resolved is None:
        return JSONResponse(
            status_code=400,
            content=error_payload(
                "VALIDATION_FAILED",
                "Không nhận ra địa điểm. Vui lòng nhập tên quận/huyện + tỉnh/thành.",
                request_id,
                field="location_raw",
            ),
        )

    district, city, lat, lng = resolved
    salary_min, salary_max = _parse_salary(body.salary_text)

    job = Job(
        company_id=hr.company_id,
        created_by=hr.id,
        title=body.title,
        salary_min_vnd=salary_min,
        salary_max_vnd=salary_max,
        salary_text=body.salary_text,
        location_raw=body.location_raw,
        location_district=district,
        location_city=city,
        location_lat=lat,
        location_lng=lng,
        start_date=body.start_date,
        shift=body.shift,
        requirements_raw=body.requirements_raw,
        target_hires=body.target_hires,
        status="draft",
    )
    db.add(job)
    await db.flush()
    await db.refresh(job)
    logger.info("job.created id=%s company=%s", job.id, hr.company_id)
    response.headers["X-Request-Id"] = request_id
    return JobResponse.model_validate(job)


@router.post("/{job_id}/generate-content", response_model=GenerateContentResponse)
async def generate_content(
    job_id: uuid.UUID,
    response: Response,
    db: AsyncSession = Depends(db_session),
    hr: HRUser = Depends(require_hr_user),
    request_id: str = Depends(get_request_id),
) -> GenerateContentResponse | dict:
    job = await db.get(Job, job_id)
    if job is None or job.company_id != hr.company_id:
        return JSONResponse(
            status_code=404,
            content=error_payload("NOT_FOUND", "Không tìm thấy việc làm.", request_id),
        )
    # Load company name for poster + content personalization
    _company = await db.get(Company, job.company_id)
    _company_name = _company.name if _company else None

    try:
        result = await generate_variants(
            db=db,
            job_id=job.id,
            title=job.title,
            salary_text=job.salary_text,
            location_district=job.location_district,
            location_city=job.location_city,
            shift=job.shift,
            start_date=job.start_date.isoformat() if job.start_date else None,
            requirements_raw=job.requirements_raw,
            target_hires=job.target_hires,
            company_name=_company_name,
        )
    except ClaudeUnavailableError:
        return JSONResponse(
            status_code=503,
            content=error_payload(
                "AI_UNAVAILABLE",
                "Dịch vụ tạo bài đăng tạm thời lỗi, thử lại sau 30 giây.",
                request_id,
            ),
        )

    # Persist variants
    persisted: list[ContentVariant] = []
    for i, v in enumerate(result["variants"], start=1):
        cv = ContentVariant(
            job_id=job.id,
            variant_index=i,
            hook_style=v["hook_style"],
            copy_vietnamese=v["copy_vietnamese"],
            generated_by_model="claude-sonnet-4-6",
            token_usage=result["token_usage"],
        )
        db.add(cv)
        persisted.append(cv)
    # Save warnings on job (edge case 4 — warn but don't block)
    job.ai_warnings = result["warnings"] or []
    await db.flush()
    for cv in persisted:
        await db.refresh(cv)

    # ─── Share-kit build ─────────────────────────────────────────────
    # Auto-create a tracking link per (variant × source). If HR has no sources
    # registered, auto-create a "direct" default so the share kit is never empty.
    all_sources_q = await db.execute(select(Source))
    all_sources = list(all_sources_q.scalars().all())
    if not all_sources:
        default_source = Source(
            channel="direct",
            external_id=None,
            display_name="Chia sẻ chung (Direct)",
        )
        db.add(default_source)
        await db.flush()
        await db.refresh(default_source)
        all_sources = [default_source]

    poster_url: str | None = None
    try:
        poster_url = generate_poster(
            job_id=job.id,
            title=job.title,
            salary_text=job.salary_text,
            location_district=job.location_district,
            location_city=job.location_city,
            target_hires=job.target_hires,
            company_name=_company_name,
        )
    except Exception:  # noqa: BLE001
        logger.exception("poster.generate.failed job_id=%s", job.id)

    share_kit: list[ShareKitItem] = []
    for cv in persisted:
        for src in all_sources:
            tid = nanoid_generate(
                "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789", size=10
            )
            link = TrackingLink(
                tracking_id=tid,
                job_id=job.id,
                variant_id=cv.id,
                source_id=src.id,
                created_by=hr.id,
            )
            db.add(link)
            share_kit.append(
                ShareKitItem(
                    source_id=src.id,
                    source_display_name=src.display_name,
                    source_channel=src.channel,
                    variant_id=cv.id,
                    tracking_id=tid,
                    copy_with_placeholder=cv.copy_vietnamese,
                    poster_url=poster_url,
                )
            )
    await db.flush()

    return GenerateContentResponse(
        variants=[ContentVariantResponse.model_validate(v) for v in persisted],
        warnings=[AIWarning.model_validate(w) for w in result["warnings"]],
        token_usage=result["token_usage"],
        share_kit=share_kit,
    )


@router.patch("/{job_id}", response_model=JobResponse)
async def patch_job(
    job_id: uuid.UUID,
    body: JobPatchRequest,
    response: Response,
    db: AsyncSession = Depends(db_session),
    hr: HRUser = Depends(require_hr_user),
    request_id: str = Depends(get_request_id),
) -> JobResponse | dict:
    job = await db.get(Job, job_id)
    if job is None or job.company_id != hr.company_id:
        return JSONResponse(
            status_code=404,
            content=error_payload("NOT_FOUND", "Không tìm thấy việc làm.", request_id),
        )

    if body.status is not None:
        job.status = body.status
        if body.status == "active" and job.published_at is None:
            from datetime import datetime, timezone
            job.published_at = datetime.now(timezone.utc)
    await db.flush()
    await db.refresh(job)
    return JobResponse.model_validate(job)
