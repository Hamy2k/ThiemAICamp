"""Minimal smoke test for app boot + healthcheck."""
from __future__ import annotations

import os

import pytest
from httpx import AsyncClient


pytestmark = pytest.mark.skipif(
    not os.getenv("TEST_DATABASE_URL"),
    reason="Requires test DB",
)


async def test_health_ok(client: AsyncClient) -> None:
    r = await client.get("/v1/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"
