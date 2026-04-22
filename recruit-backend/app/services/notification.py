"""Telegram notification sender."""
from __future__ import annotations

import logging
import uuid
from typing import Any

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db.models import NotificationLog

logger = logging.getLogger(__name__)


async def send_telegram_new_match(
    session: AsyncSession,
    *,
    chat_id: str,
    match_id: uuid.UUID,
    lead_id: uuid.UUID,
    job_id: uuid.UUID,
    text: str,
) -> bool:
    """Send a Telegram message to HR's chat_id. Returns True on success.

    Logs attempt to notifications_log. Has timeout per constraint.
    """
    settings = get_settings()
    token = settings.telegram_bot_token
    if not token:
        logger.warning("telegram.send.skipped reason=no_token", extra={"match_id": str(match_id)})
        _log(session, chat_id, match_id, lead_id, job_id, {"text": text}, "failed", "no_token")
        return False

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    try:
        async with httpx.AsyncClient(timeout=settings.telegram_timeout_seconds) as client:
            r = await client.post(url, json=payload)
        if r.status_code == 200:
            _log(session, chat_id, match_id, lead_id, job_id, payload, "sent", None)
            return True
        _log(session, chat_id, match_id, lead_id, job_id, payload, "failed", f"http_{r.status_code}:{r.text[:200]}")
        return False
    except (httpx.TimeoutException, httpx.HTTPError) as exc:
        _log(session, chat_id, match_id, lead_id, job_id, payload, "failed", str(exc)[:300])
        return False


def _log(
    session: AsyncSession,
    recipient: str,
    match_id: uuid.UUID,
    lead_id: uuid.UUID,
    job_id: uuid.UUID,
    payload: dict[str, Any],
    status: str,
    err: str | None,
) -> None:
    entry = NotificationLog(
        channel="telegram",
        recipient=recipient,
        match_id=match_id,
        lead_id=lead_id,
        job_id=job_id,
        payload=payload,
        status=status,
        error_message=err,
    )
    session.add(entry)


def format_new_match_message(
    *,
    lead_name: str,
    phone_masked: str,
    area: str | None,
    score_total: float,
    tier: str,
    explanation_vi: str,
) -> str:
    """Vietnamese-language Telegram notification."""
    area_line = area or "(không rõ khu vực)"
    return (
        f"<b>🔔 Ứng viên mới — {tier.upper()}</b>\n"
        f"Tên: {lead_name}\n"
        f"SĐT: <code>{phone_masked}</code>\n"
        f"Khu vực: {area_line}\n"
        f"Điểm: <b>{score_total:.0f}/100</b>\n"
        f"— {explanation_vi}"
    )
