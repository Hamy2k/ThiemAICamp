"""Public lead submit endpoint.

Edge cases handled:
- 1 (duplicate phone): returns 409 with resume_session_id (test_duplicate_phone_merges_history)
- 5 (non-accent VN): area_raw normalized via LLM/landmark (test_accent_normalization)
- 6 (phone formats): normalized to E.164 via app.utils.phone (test_phone_normalization_e164)
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Request, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import db_session, error_payload, get_request_id
from app.db.models import ConsentRecord, Job, Lead, ScreeningSession, TrackingLink
from app.schemas.common import ErrorResponse
from app.schemas.lead import DeletionResponse, LeadCreateRequest, LeadCreateResponse, NormalizedLeadInfo
from app.services.gazetteer import search_by_fuzzy_name
from app.services.scoring import haversine_km
from app.utils.idempotency import fingerprint, get_store
from app.utils.phone import InvalidPhoneError, normalize_phone_e164
from app.utils.vietnamese import nfc

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/leads", tags=["leads"])


CONSENT_TEXT_VI = (
    "Tôi đồng ý cho nền tảng sử dụng thông tin cá nhân (họ tên, số điện thoại, khu vực) "
    "để kết nối với nhà tuyển dụng theo quy định của Nghị định 13/2023/NĐ-CP."
)


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=LeadCreateResponse,
    responses={409: {"model": ErrorResponse}, 422: {"model": ErrorResponse}},
)
async def create_lead(
    body: LeadCreateRequest,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(db_session),
    request_id: str = Depends(get_request_id),
) -> LeadCreateResponse | dict:
    # Consent required
    if not body.consent.accepted:
        response.status_code = 422
        return error_payload(
            "CONSENT_REQUIRED",
            "Vui lòng tích ô đồng ý để tiếp tục.",
            request_id,
            field="consent.accepted",
        )

    # Phone normalization (edge case 6)
    try:
        phone_e164 = normalize_phone_e164(body.phone)
    except InvalidPhoneError:
        response.status_code = 400
        return error_payload(
            "VALIDATION_FAILED",
            "Số điện thoại không hợp lệ. Vui lòng nhập lại.",
            request_id,
            field="phone",
        )

    # Resolve tracking link to derive job + variant + source
    job: Job | None = None
    source_channel = "unknown"
    source_id: uuid.UUID | None = None
    variant_id: uuid.UUID | None = None
    campaign_id: uuid.UUID | None = None
    tlink: TrackingLink | None = None

    if body.tracking_id:
        tlink = await db.get(TrackingLink, body.tracking_id)
        if tlink is None:
            response.status_code = 400
            return error_payload(
                "VALIDATION_FAILED",
                "Link theo dõi không tồn tại.",
                request_id,
                field="tracking_id",
            )
        job = await db.get(Job, tlink.job_id)
        variant_id = tlink.variant_id
        source_id = tlink.source_id
        campaign_id = tlink.campaign_id
        # Pull channel from source
        from app.db.models import Source
        src = await db.get(Source, tlink.source_id)
        if src is not None:
            source_channel = src.channel

    if job is None:
        response.status_code = 400
        return error_payload(
            "VALIDATION_FAILED",
            "Không xác định được việc làm đang ứng tuyển.",
            request_id,
            field="tracking_id",
        )

    # Idempotency — same phone + same job within window → merge
    store = get_store()
    fp = fingerprint(phone_e164, str(job.id))
    prior = store.get(fp)

    # Dedupe — check existing primary lead for this phone (edge case 1)
    existing_stmt = select(Lead).where(
        Lead.phone_e164 == phone_e164,
        Lead.is_duplicate_of.is_(None),
    )
    existing = (await db.execute(existing_stmt)).scalar_one_or_none()

    if existing is not None:
        # If a session already exists for this job → 409 with resume info
        session_stmt = select(ScreeningSession).where(
            ScreeningSession.lead_id == existing.id,
            ScreeningSession.job_id == job.id,
        )
        existing_session = (await db.execute(session_stmt)).scalar_one_or_none()
        if existing_session is not None:
            response.status_code = 409
            return error_payload(
                "DUPLICATE_PHONE",
                "Số điện thoại này đã đăng ký. Tiếp tục trò chuyện.",
                request_id,
                details={"resume_session_id": str(existing_session.id)},
            )
        # Merge: reuse existing primary record, create new session for this job
        session = _new_session(existing.id, job.id)
        db.add(session)
        await db.flush()
        await db.refresh(session)
        return _build_response(existing, session, job)

    # Normalize area (edge case 5)
    area_normalized: str | None = None
    area_district: str | None = None
    area_city: str | None = None
    area_lat = None
    area_lng = None
    distance_km: float | None = None
    if body.area_raw:
        nfc_area = nfc(body.area_raw)
        resolved = search_by_fuzzy_name(nfc_area)
        if resolved is not None:
            area_district, area_city, area_lat, area_lng = resolved
            area_normalized = f"{area_district}, {area_city}"
            distance_km = haversine_km(
                float(area_lat), float(area_lng),
                float(job.location_lat), float(job.location_lng),
            )

    # Consent first — deferred FK resolved in transaction
    now = datetime.now(timezone.utc)
    lead = Lead(
        phone_e164=phone_e164,
        phone_raw=body.phone,
        full_name=body.full_name.strip(),
        area_raw=body.area_raw,
        area_normalized=area_normalized,
        area_district=area_district,
        area_city=area_city,
        area_lat=area_lat,
        area_lng=area_lng,
        source_channel=source_channel,
        source_id=source_id,
        variant_id=variant_id,
        tracking_id=body.tracking_id,
        campaign_id=campaign_id,
        entry_job_id=job.id,
        user_agent=request.headers.get("user-agent"),
        ip_address=request.client.host if request.client else None,
    )
    db.add(lead)
    await db.flush()

    consent = ConsentRecord(
        lead_id=lead.id,
        consent_version=body.consent.version,
        consent_text_vi=CONSENT_TEXT_VI,
        purposes={"screening": True, "matching": True, "analytics": False, "marketing": False},
        granted_at=now,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    db.add(consent)
    await db.flush()
    lead.consent_record_id = consent.id

    session = _new_session(lead.id, job.id)
    db.add(session)
    await db.flush()
    await db.refresh(session)

    store.set(fp, str(session.id))
    logger.info("lead.created id=%s job=%s distance_km=%s", lead.id, job.id, distance_km)

    return _build_response(lead, session, job, distance_km=distance_km)


def _new_session(lead_id: uuid.UUID, job_id: uuid.UUID) -> ScreeningSession:
    return ScreeningSession(
        lead_id=lead_id,
        job_id=job_id,
        status="in_progress",
        turn_count=0,
        extracted_data={},
    )


def _build_response(
    lead: Lead,
    session: ScreeningSession,
    job: Job,
    *,
    distance_km: float | None = None,
) -> LeadCreateResponse:
    first_name = lead.full_name.split()[0] if lead.full_name else "bạn"
    first_msg = (
        f"Chào anh/chị {first_name}! Em là trợ lý tuyển dụng 🤖. "
        f"Em hỏi nhanh vài câu để kết nối anh/chị với nhà tuyển dụng nhé. "
        f"Anh/chị đi làm được từ khi nào ạ?"
    )
    return LeadCreateResponse(
        lead_id=lead.id,
        session_id=session.id,
        normalized=NormalizedLeadInfo(
            phone_e164=lead.phone_e164,
            area_normalized=lead.area_normalized,
            distance_km=distance_km,
        ),
        first_ai_message=first_msg,
    )


@router.delete("/{lead_id}", response_model=DeletionResponse)
async def delete_lead(
    lead_id: uuid.UUID,
    db: AsyncSession = Depends(db_session),
) -> DeletionResponse:
    """PDPD right-to-deletion. Calls stored proc (redacts, preserves referential integrity)."""
    from sqlalchemy import text as sa_text
    await db.execute(sa_text("SELECT pdpd_delete_lead(:lid)"), {"lid": str(lead_id)})
    return DeletionResponse(deleted=True, deleted_at=datetime.now(timezone.utc))
