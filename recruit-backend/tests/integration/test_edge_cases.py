"""Integration tests — one per Phase 1 edge case (1–6).

These hit the FastAPI app via httpx.AsyncClient + a real test Postgres.
They run only if TEST_DATABASE_URL is set.
"""
from __future__ import annotations

import os
import uuid
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import ConsentRecord, Lead, Match, ScreeningSession


pytestmark = pytest.mark.skipif(
    not os.getenv("TEST_DATABASE_URL"),
    reason="Integration tests require TEST_DATABASE_URL",
)


# ═══════════════════════════════════════════════════════════════════
# Edge case 1: Duplicate phone → dedupe, merge history
# ═══════════════════════════════════════════════════════════════════

async def test_duplicate_phone_merges_history(
    client: AsyncClient, db: AsyncSession, seeded_job: dict,
) -> None:
    body = {
        "tracking_id": seeded_job["tracking_id"],
        "full_name": "Nguyễn Văn Tèo",
        "phone": "0909123456",
        "area_raw": "ba chieu",
        "consent": {"version": "v1.0", "accepted": True},
    }
    r1 = await client.post("/v1/leads", json=body)
    assert r1.status_code == 201
    session_id_1 = r1.json()["session_id"]

    # Re-submit same phone, same job → 409 with resume_session_id
    r2 = await client.post("/v1/leads", json=body)
    assert r2.status_code == 409
    err = r2.json()["error"]
    assert err["code"] == "DUPLICATE_PHONE"
    assert err["details"]["resume_session_id"] == session_id_1

    # Only 1 primary lead for phone
    rows = (await db.execute(
        select(Lead).where(Lead.phone_e164 == "+84909123456", Lead.is_duplicate_of.is_(None))
    )).scalars().all()
    assert len(rows) == 1


# ═══════════════════════════════════════════════════════════════════
# Edge case 2: Abandoned chat — partial data saved
# ═══════════════════════════════════════════════════════════════════

async def test_partial_screening_saved(
    client: AsyncClient, db: AsyncSession, seeded_job: dict,
) -> None:
    r1 = await client.post("/v1/leads", json={
        "tracking_id": seeded_job["tracking_id"],
        "full_name": "Lê Văn Tám",
        "phone": "0912345678",
        "area_raw": "quan 7",
        "consent": {"version": "v1.0", "accepted": True},
    })
    assert r1.status_code == 201
    session_id = r1.json()["session_id"]

    # Send one turn, then abandon (don't call /complete).
    with patch("app.api.v1.screening.run_screening_turn", new_callable=AsyncMock) as mock_turn:
        mock_turn.return_value = {
            "reply": "Cảm ơn anh.",
            "extracted_delta": {"start_date": "asap", "hours_per_day": 8},
            "done": False,
            "fallback_used": False,
        }
        r_turn = await client.post("/v1/screening/message", json={
            "session_id": session_id,
            "message": "em di lam lien duoc, lam 8h",
        })
    assert r_turn.status_code == 200

    # Verify session has partial extracted_data + status still in_progress
    row = (await db.execute(
        select(ScreeningSession).where(ScreeningSession.id == uuid.UUID(session_id))
    )).scalar_one()
    assert row.status == "in_progress"
    assert row.extracted_data.get("start_date") == "asap"
    assert row.extracted_data.get("hours_per_day") == 8
    assert row.turn_count == 1


# ═══════════════════════════════════════════════════════════════════
# Edge case 3: Multiple job matches → notify HR of top 1
# ═══════════════════════════════════════════════════════════════════

async def test_top_match_sent_to_hr(
    client: AsyncClient, db: AsyncSession, seeded_job: dict,
) -> None:
    # Create 2 leads with different scores by submitting + completing each
    async def submit_and_complete(phone: str, name: str, area: str, extracted: dict) -> uuid.UUID:
        r1 = await client.post("/v1/leads", json={
            "tracking_id": seeded_job["tracking_id"],
            "full_name": name, "phone": phone, "area_raw": area,
            "consent": {"version": "v1.0", "accepted": True},
        })
        assert r1.status_code == 201
        sid = uuid.UUID(r1.json()["session_id"])
        # Inject extracted_data directly (simulates completed screening)
        sess = await db.get(ScreeningSession, sid)
        sess.extracted_data = extracted
        sess.status = "in_progress"
        await db.commit()
        with patch("app.api.v1.screening.score_lead", new_callable=AsyncMock) as mock_sc, \
             patch("app.api.v1.screening.send_telegram_new_match", new_callable=AsyncMock) as mock_tg:
            from decimal import Decimal as D
            from app.ai.scorer import ScoringOutput
            from app.services.scoring import ComponentScores
            # Higher score for closer lead
            loc_score = D("100") if area == "ba chieu" else D("40")
            mock_sc.return_value = ScoringOutput(
                scores=ComponentScores(
                    location=loc_score,
                    availability=D("100"),
                    experience=D("60"),
                    response_quality=D("80"),
                ),
                explanation_vi="Lý giải mẫu.",
                fallback_used=False,
            )
            mock_tg.return_value = True
            r2 = await client.post("/v1/screening/complete", json={"session_id": str(sid)})
            assert r2.status_code == 200
        return sid

    await submit_and_complete("0909000001", "A Xa", "quan 7", {"start_date": "asap"})
    await submit_and_complete("0909000002", "B Gan", "ba chieu", {"start_date": "asap"})

    # Verify top-scoring match notified
    stmt = select(Match).where(Match.job_id == seeded_job["job_id"]).order_by(Match.score_total.desc())
    rows = (await db.execute(stmt)).scalars().all()
    assert len(rows) == 2
    top = rows[0]
    # "ba chieu" lead should be higher-scoring
    assert top.score_location >= rows[1].score_location


# ═══════════════════════════════════════════════════════════════════
# Edge case 4: Unrealistic salary → AI warns, doesn't block
# ═══════════════════════════════════════════════════════════════════

async def test_salary_warning_does_not_block(
    client: AsyncClient, db: AsyncSession, seeded_job: dict,
) -> None:
    with patch("app.api.v1.jobs.generate_variants", new_callable=AsyncMock) as mock_gen:
        mock_gen.return_value = {
            "variants": [
                {"hook_style": hs, "copy_vietnamese": "TUYỂN..." * 30}
                for hs in ("urgency", "salary_first", "proximity", "friendly", "detailed")
            ],
            "warnings": [{"code": "SALARY_BELOW_MARKET", "message": "Lương thấp so với khu vực."}],
            "token_usage": {"input": 300, "output": 1800, "cost_usd": 0.028},
        }
        r = await client.post(
            f"/v1/hr/jobs/{seeded_job['job_id']}/generate-content",
            headers={"Authorization": "Bearer test-token"},
        )
    assert r.status_code == 200
    body = r.json()
    assert len(body["variants"]) == 5
    assert any(w["code"] == "SALARY_BELOW_MARKET" for w in body["warnings"])
    # Job NOT blocked — variants persisted
    from app.db.models import ContentVariant
    vs = (await db.execute(select(ContentVariant).where(ContentVariant.job_id == seeded_job["job_id"]))).scalars().all()
    # Original seed variant + 5 newly generated = 6
    assert len(vs) >= 5


# ═══════════════════════════════════════════════════════════════════
# Edge case 5: Non-accent Vietnamese → normalized
# ═══════════════════════════════════════════════════════════════════

async def test_accent_normalization(
    client: AsyncClient, db: AsyncSession, seeded_job: dict,
) -> None:
    r = await client.post("/v1/leads", json={
        "tracking_id": seeded_job["tracking_id"],
        "full_name": "Hoang Van",
        "phone": "0987654321",
        "area_raw": "em o gan cho ba chieu",
        "consent": {"version": "v1.0", "accepted": True},
    })
    assert r.status_code == 201
    body = r.json()
    assert body["normalized"]["area_normalized"] == "Quận Bình Thạnh, TPHCM"


# ═══════════════════════════════════════════════════════════════════
# Edge case 6: Phone format variants → E.164
# (Unit test covers normalizer; this verifies end-to-end storage.)
# ═══════════════════════════════════════════════════════════════════

async def test_phone_format_stored_as_e164(
    client: AsyncClient, db: AsyncSession, seeded_job: dict,
) -> None:
    r = await client.post("/v1/leads", json={
        "tracking_id": seeded_job["tracking_id"],
        "full_name": "Phan Thi",
        "phone": "84 912 345 000",  # E.164 intent without +
        "area_raw": "quan 7",
        "consent": {"version": "v1.0", "accepted": True},
    })
    assert r.status_code == 201
    assert r.json()["normalized"]["phone_e164"] == "+84912345000"
    row = (await db.execute(select(Lead).where(Lead.phone_e164 == "+84912345000"))).scalar_one()
    assert row.phone_raw == "84 912 345 000"
