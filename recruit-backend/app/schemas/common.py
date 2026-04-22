"""Common response envelopes + error format (per Phase 1 spec)."""
from __future__ import annotations

from typing import Any, Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field


class ErrorDetail(BaseModel):
    code: str = Field(description="Stable error code, e.g. VALIDATION_FAILED")
    message: str = Field(description="User-facing message in Vietnamese")
    field: str | None = None
    details: dict[str, Any] | None = None
    request_id: str


class ErrorResponse(BaseModel):
    error: ErrorDetail


T = TypeVar("T")


class CursorPage(BaseModel, Generic[T]):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    items: list[T]
    next_cursor: str | None = None
