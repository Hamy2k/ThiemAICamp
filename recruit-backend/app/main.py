"""FastAPI application factory."""
from __future__ import annotations

import logging
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api.deps import get_request_id
from app.api.v1 import (
    analytics,
    health,
    hr_jobs,
    hr_leads,
    hr_sources,
    jobs,
    leads,
    screening,
    tracking,
)
from app.config import get_settings
from app.utils.logging import setup_logging


def create_app() -> FastAPI:
    settings = get_settings()
    setup_logging(settings.log_level)

    app = FastAPI(
        title="Recruit API",
        version="0.1.0",
        description="AI-powered job distribution for blue-collar hiring in Vietnam.",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register routers — all under /v1 prefix
    app.include_router(health.router, prefix="/v1")
    app.include_router(jobs.router, prefix="/v1")
    app.include_router(leads.router, prefix="/v1")
    app.include_router(screening.router, prefix="/v1")
    app.include_router(tracking.router, prefix="/v1")
    app.include_router(analytics.router, prefix="/v1")
    app.include_router(hr_leads.router, prefix="/v1")
    app.include_router(hr_jobs.router, prefix="/v1")
    app.include_router(hr_sources.router, prefix="/v1")

    # Static: auto-generated job posters for HR to attach when posting to FB
    posters_dir = Path(__file__).resolve().parent.parent / "public" / "posters"
    posters_dir.mkdir(parents=True, exist_ok=True)
    app.mount("/posters", StaticFiles(directory=str(posters_dir)), name="posters")

    @app.exception_handler(Exception)
    async def unhandled(request: Request, exc: Exception) -> JSONResponse:
        rid = request.headers.get("X-Request-Id", "req_unknown")
        logging.getLogger(__name__).exception("unhandled.error request_id=%s", rid)
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "Đã có lỗi xảy ra. Vui lòng thử lại.",
                    "request_id": rid,
                }
            },
        )

    return app


app = create_app()
