"""Shared FastAPI dependencies: auth, request_id, error helpers."""
from __future__ import annotations

import uuid
from collections.abc import AsyncIterator

from fastapi import Depends, Header, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import HRUser
from app.db.session import get_db


async def get_request_id(request: Request) -> str:
    """Extract or generate a request id for error correlation."""
    rid = request.headers.get("X-Request-Id")
    if not rid:
        rid = f"req_{uuid.uuid4().hex[:16]}"
    return rid


def error_payload(code: str, message_vi: str, request_id: str, *, field: str | None = None, details: dict | None = None) -> dict:
    """Build error envelope in Phase 1 spec format."""
    err: dict = {"code": code, "message": message_vi, "request_id": request_id}
    if field is not None:
        err["field"] = field
    if details is not None:
        err["details"] = details
    return {"error": err}


async def require_hr_user(
    authorization: str | None = Header(default=None),
    db: AsyncSession = Depends(get_db),
) -> HRUser:
    """Very basic bearer auth: token == hr_users.api_key_hash (MVP).

    Production: use bcrypt.checkpw on a raw token and indexed prefix.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Thiếu Authorization header.",
        )
    token = authorization.removeprefix("Bearer ").strip()
    if not token:
        raise HTTPException(status_code=401, detail="Token rỗng.")
    result = await db.execute(select(HRUser).where(HRUser.api_key_hash == token))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=401, detail="Token không hợp lệ.")
    return user


async def db_session() -> AsyncIterator[AsyncSession]:
    """Pass-through wrapper so routers depend on one name."""
    async for s in get_db():
        yield s
