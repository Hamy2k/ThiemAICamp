"""Screening chat endpoints (per-turn + complete)."""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from decimal import Decimal

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.screener import run_screening_turn
from app.ai.scorer import score_lead
from app.api.deps import db_session, error_payload, get_request_id
from app.db.models import HRUser, Job, Lead, Match, ScreeningMessage, ScreeningSession
from app.schemas.screening import (
    ExtractedDelta,
    ScoreBreakdown,
    ScreeningCompleteRequest,
    ScreeningCompleteResponse,
    ScreeningTurnRequest,
    ScreeningTurnResponse,
)
from app.services.matching import top_match_for_job
from app.services.notification import format_new_match_message, send_telegram_new_match
from app.services.scoring import compute_tier

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/screening", tags=["screening"])

MAX_TURNS = 5


@router.post("/message", response_model=ScreeningTurnResponse)
async def screening_turn(
    body: ScreeningTurnRequest,
    response: Response,
    db: AsyncSession = Depends(db_session),
    request_id: str = Depends(get_request_id),
) -> ScreeningTurnResponse | dict:
    session = await db.get(ScreeningSession, body.session_id)
    if session is None:
        response.status_code = 404
        return error_payload("NOT_FOUND", "Phiên trò chuyện không tồn tại.", request_id)
    if session.status != "in_progress":
        response.status_code = 410
        return error_payload(
            "SCREENING_EXHAUSTED",
            "Phiên đã kết thúc.",
            request_id,
            details={"next_action": "complete"},
        )
    if session.turn_count >= MAX_TURNS:
        response.status_code = 410
        return error_payload(
            "SCREENING_EXHAUSTED",
            "Đã đủ thông tin, đang gửi cho nhà tuyển dụng.",
            request_id,
            details={"next_action": "complete"},
        )

    job = await db.get(Job, session.job_id)
    if job is None:
        response.status_code = 404
        return error_payload("NOT_FOUND", "Việc làm không tồn tại.", request_id)

    # Record user message
    user_msg = ScreeningMessage(
        session_id=session.id,
        turn_index=session.turn_count + 1,
        role="user",
        content=body.message,
    )
    db.add(user_msg)

    # Load prior history
    history_stmt = (
        select(ScreeningMessage)
        .where(ScreeningMessage.session_id == session.id)
        .order_by(ScreeningMessage.turn_index)
    )
    history_rows = (await db.execute(history_stmt)).scalars().all()
    history = [{"role": m.role, "content": m.content} for m in history_rows]

    job_ctx = {
        "title": job.title,
        "location_district": job.location_district,
        "location_city": job.location_city,
        "shift": job.shift,
        "requirements_raw": job.requirements_raw,
    }

    ai_result = await run_screening_turn(
        db=db,
        session_id=session.id,
        job_context=job_ctx,
        extracted_so_far=session.extracted_data or {},
        turn_index=session.turn_count + 1,
        history=history,
        user_message=body.message,
    )

    # Merge extracted. Drop only None / empty dict (no data). Empty list `[]` IS data
    # (e.g. questions_from_candidate=[] means user answered "no questions").
    merged = dict(session.extracted_data or {})
    for k, v in (ai_result["extracted_delta"] or {}).items():
        if v is None:
            continue
        if isinstance(v, dict) and not v:
            continue
        merged[k] = v
    # SQLAlchemy JSONB mutation tracking: reassign to ensure UPDATE is emitted.
    session.extracted_data = merged
    from sqlalchemy.orm.attributes import flag_modified
    flag_modified(session, "extracted_data")
    session.turn_count += 1
    session.last_turn_at = datetime.now(timezone.utc)
    if ai_result["done"] or session.turn_count >= MAX_TURNS:
        session.status = "completed"
        session.completed_at = session.last_turn_at

    # Record assistant message
    asst_msg = ScreeningMessage(
        session_id=session.id,
        turn_index=session.turn_count,
        role="assistant",
        content=ai_result["reply"],
    )
    db.add(asst_msg)

    return ScreeningTurnResponse(
        turn_index=session.turn_count,
        reply=ai_result["reply"],
        extracted_delta=ExtractedDelta.model_validate(ai_result["extracted_delta"] or {}),
        turns_remaining=max(0, MAX_TURNS - session.turn_count),
        done=session.status == "completed",
    )


@router.post("/complete", response_model=ScreeningCompleteResponse)
async def screening_complete(
    body: ScreeningCompleteRequest,
    response: Response,
    db: AsyncSession = Depends(db_session),
    request_id: str = Depends(get_request_id),
) -> ScreeningCompleteResponse | dict:
    """Finalize scoring + create Match + queue HR notification (edge case 3)."""
    session = await db.get(ScreeningSession, body.session_id)
    if session is None:
        response.status_code = 404
        return error_payload("NOT_FOUND", "Phiên không tồn tại.", request_id)

    # Idempotent: return existing match if already completed
    existing_match_stmt = select(Match).where(
        Match.lead_id == session.lead_id, Match.job_id == session.job_id
    )
    existing_match = (await db.execute(existing_match_stmt)).scalar_one_or_none()
    if existing_match is not None:
        return _match_to_response(existing_match)

    lead = await db.get(Lead, session.lead_id)
    job = await db.get(Job, session.job_id)
    if lead is None or job is None:
        response.status_code = 404
        return error_payload("NOT_FOUND", "Thiếu dữ liệu lead hoặc việc làm.", request_id)

    # Distance
    from app.services.scoring import haversine_km
    distance_km: float | None = None
    if lead.area_lat and lead.area_lng:
        distance_km = haversine_km(
            float(lead.area_lat), float(lead.area_lng),
            float(job.location_lat), float(job.location_lng),
        )

    keywords = (job.requirements_parsed or {}).get("keywords", []) if job.requirements_parsed else []
    exp_required = bool((job.requirements_parsed or {}).get("exp_required", False))

    scoring = await score_lead(
        db=db,
        session_id=session.id,
        distance_km=distance_km,
        job_shift=job.shift,
        exp_required=exp_required,
        keywords=keywords,
        extracted=session.extracted_data or {},
    )

    total = scoring.scores.total()
    tier = compute_tier(total)

    match = Match(
        lead_id=lead.id,
        job_id=job.id,
        session_id=session.id,
        score_total=total,
        score_location=scoring.scores.location,
        score_availability=scoring.scores.availability,
        score_experience=scoring.scores.experience,
        score_response_quality=scoring.scores.response_quality,
        explanation_vi=scoring.explanation_vi,
        tier=tier,
        distance_km=Decimal(str(round(distance_km, 2))) if distance_km is not None else None,
    )
    db.add(match)

    session.status = "completed"
    session.completed_at = datetime.now(timezone.utc)
    await db.flush()
    await db.refresh(match)

    # Notify HR if this is top match for the job (edge case 3)
    top = await top_match_for_job(db, job.id)
    if top is not None and top.id == match.id:
        from app.utils.phone import mask_phone
        from app.db.models import HRUser as _HR
        hr_stmt = select(_HR).where(
            _HR.company_id == job.company_id, _HR.telegram_chat_id.isnot(None)
        ).limit(1)
        hr = (await db.execute(hr_stmt)).scalar_one_or_none()
        if hr and hr.telegram_chat_id:
            msg_text = format_new_match_message(
                lead_name=lead.full_name,
                phone_masked=mask_phone(lead.phone_e164),
                area=lead.area_normalized,
                score_total=float(total),
                tier=tier,
                explanation_vi=scoring.explanation_vi,
            )
            ok = await send_telegram_new_match(
                session=db,
                chat_id=hr.telegram_chat_id,
                match_id=match.id,
                lead_id=lead.id,
                job_id=job.id,
                text=msg_text,
            )
            if ok:
                match.notified_hr = True
                match.notified_at = datetime.now(timezone.utc)

    return _match_to_response(match, fallback_used=scoring.fallback_used)


def _match_to_response(match: Match, *, fallback_used: bool = False) -> ScreeningCompleteResponse:
    return ScreeningCompleteResponse(
        match_id=match.id,
        score_total=match.score_total,
        score_breakdown=ScoreBreakdown(
            location=match.score_location,
            availability=match.score_availability,
            experience=match.score_experience,
            response_quality=match.score_response_quality,
        ),
        tier=match.tier,  # type: ignore[arg-type]
        explanation_vi=match.explanation_vi,
        thank_you_message="Cảm ơn anh/chị. Nhà tuyển dụng sẽ liên hệ lại sớm 📞",
        fallback_used=fallback_used,
    )
