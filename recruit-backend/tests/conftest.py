"""Shared test fixtures.

Integration tests run against a real Postgres 15 via TEST_DATABASE_URL.
Unit tests have no external deps.
"""
from __future__ import annotations

import asyncio
import os
import uuid
from collections.abc import AsyncIterator
from decimal import Decimal

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db.base import Base
from app.db import models  # noqa: F401 — registers metadata


TEST_DB_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/recruit_test",
)

# Set DATABASE_URL before importing app so get_db() uses test DB
os.environ["DATABASE_URL"] = TEST_DB_URL
os.environ.setdefault("ANTHROPIC_API_KEY", "test-key")


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def engine():
    eng = create_async_engine(TEST_DB_URL, echo=False)
    # Run migration SQL inline (avoids alembic subprocess in tests)
    from alembic.config import Config
    from alembic import command
    cfg = Config("alembic.ini")
    cfg.set_main_option("sqlalchemy.url", TEST_DB_URL)
    async with eng.begin() as conn:
        await conn.run_sync(lambda c: None)  # connectivity sanity
    # Apply migration via alembic for realism
    try:
        command.upgrade(cfg, "head")
    except Exception:
        # Fallback: create_all from metadata if alembic not configured in test env
        async with eng.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    yield eng
    await eng.dispose()


@pytest_asyncio.fixture
async def db(engine) -> AsyncIterator[AsyncSession]:
    Session = async_sessionmaker(engine, expire_on_commit=False)
    async with Session() as session:
        # Clean all tables for test isolation
        for t in (
            "ai_calls", "notifications_log", "matches",
            "screening_messages", "screening_sessions",
            "consent_records", "leads",
            "link_clicks", "tracking_links", "campaigns", "sources",
            "content_variants", "jobs", "hr_users", "companies",
        ):
            await session.execute(text(f"TRUNCATE TABLE {t} CASCADE"))
        await session.commit()
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def seeded_job(db: AsyncSession) -> dict:
    """Insert a company + HR + active job + variant + source + tracking_link."""
    from app.db.models import Company, ContentVariant, HRUser, Job, Source, TrackingLink
    c = Company(name="ABC Plastics")
    db.add(c); await db.flush()
    hr = HRUser(
        company_id=c.id, email="hr@abc.vn", full_name="HR One",
        api_key_hash="test-token", telegram_chat_id=None,
    )
    db.add(hr); await db.flush()
    job = Job(
        company_id=c.id, created_by=hr.id,
        title="Công nhân ép nhựa",
        salary_text="8-10 triệu",
        salary_min_vnd=8_000_000, salary_max_vnd=10_000_000,
        location_raw="KCN Sóng Thần, Dĩ An",
        location_district="Thành phố Dĩ An",
        location_city="Bình Dương",
        location_lat=Decimal("10.9042"), location_lng=Decimal("106.7662"),
        shift="rotating",
        requirements_parsed={"exp_required": False, "keywords": ["ep nhua", "ca dem"]},
        status="active",
    )
    db.add(job); await db.flush()
    variant = ContentVariant(
        job_id=job.id, variant_index=1, hook_style="urgency",
        copy_vietnamese="TUYỂN GẤP...", generated_by_model="claude-sonnet-4-6",
        token_usage={"input": 300, "output": 1800, "cost_usd": 0.028},
    )
    db.add(variant); await db.flush()
    source = Source(channel="facebook", external_id="tphcm", display_name="Việc làm TPHCM")
    db.add(source); await db.flush()
    tid = "testABC123"
    tlink = TrackingLink(
        tracking_id=tid, job_id=job.id, variant_id=variant.id,
        source_id=source.id, created_by=hr.id,
    )
    db.add(tlink); await db.commit()
    return {
        "company_id": c.id, "hr_id": hr.id, "hr_token": "test-token",
        "job_id": job.id, "variant_id": variant.id, "source_id": source.id,
        "tracking_id": tid,
    }


@pytest_asyncio.fixture
async def client(engine) -> AsyncIterator[AsyncClient]:
    # Re-import app AFTER env is set so it picks up test DB URL
    from app.main import app
    from app.db.session import AsyncSessionLocal, engine as app_engine
    # Point app's engine at our test engine via monkeypatch: they point at same URL already.
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
