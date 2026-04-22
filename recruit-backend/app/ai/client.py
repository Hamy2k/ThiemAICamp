"""Claude API client with retry + cost tracking.

Retry: 1x on 5xx / APITimeoutError / APIConnectionError with 500ms backoff (configurable).
Cost: persists each call to ai_calls table.
"""
from __future__ import annotations

import asyncio
import logging
import time
import uuid
from dataclasses import dataclass
from decimal import Decimal
from typing import Any

import anthropic
from anthropic import APIConnectionError, APIError, APIStatusError, APITimeoutError
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db.models import AICall

logger = logging.getLogger(__name__)


# Pricing per million tokens (USD). Update if Anthropic changes rates.
_PRICING: dict[str, dict[str, float]] = {
    "claude-sonnet-4-6":          {"input": 3.00, "cached": 0.30, "output": 15.00},
    "claude-haiku-4-5-20251001":  {"input": 1.00, "cached": 0.10, "output": 5.00},
}


@dataclass
class AIResult:
    content: list[Any]
    input_tokens: int
    cached_tokens: int
    output_tokens: int
    cost_usd: Decimal
    latency_ms: int
    stop_reason: str


class ClaudeUnavailableError(Exception):
    """Raised after all retries fail."""


class ClaudeClient:
    """Thin wrapper with retry + accounting."""

    def __init__(self) -> None:
        s = get_settings()
        kwargs: dict[str, Any] = {
            "api_key": s.anthropic_api_key or "missing-key",
            "timeout": s.claude_timeout_seconds,
        }
        if s.ai_gateway_base_url:
            kwargs["base_url"] = s.ai_gateway_base_url
        self._client = anthropic.AsyncAnthropic(**kwargs)
        self._retries = s.claude_retry_count
        self._backoff_ms = s.claude_retry_backoff_ms

    async def call(
        self,
        *,
        model: str,
        system: str | list[dict[str, Any]],
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        tool_choice: dict[str, Any] | None = None,
        max_tokens: int = 1024,
        call_site: str,
        related_id: uuid.UUID | None = None,
        db: AsyncSession | None = None,
    ) -> AIResult:
        """Call Claude with retry; persist usage if db session given."""
        last_err: Exception | None = None
        attempts = self._retries + 1
        started = time.monotonic()

        for attempt in range(1, attempts + 1):
            try:
                kwargs: dict[str, Any] = {
                    "model": model,
                    "max_tokens": max_tokens,
                    "system": system,
                    "messages": messages,
                }
                if tools:
                    kwargs["tools"] = tools
                if tool_choice:
                    kwargs["tool_choice"] = tool_choice

                resp = await self._client.messages.create(**kwargs)
                latency_ms = int((time.monotonic() - started) * 1000)

                usage = resp.usage
                input_tokens = usage.input_tokens
                cached_tokens = getattr(usage, "cache_read_input_tokens", 0) or 0
                output_tokens = usage.output_tokens
                cost = _compute_cost(model, input_tokens, cached_tokens, output_tokens)

                if db is not None:
                    db.add(
                        AICall(
                            call_site=call_site,
                            model=model,
                            input_tokens=input_tokens,
                            cached_tokens=cached_tokens,
                            output_tokens=output_tokens,
                            cost_usd=cost,
                            latency_ms=latency_ms,
                            related_id=related_id,
                            error_code=None,
                        )
                    )

                return AIResult(
                    content=list(resp.content),
                    input_tokens=input_tokens,
                    cached_tokens=cached_tokens,
                    output_tokens=output_tokens,
                    cost_usd=cost,
                    latency_ms=latency_ms,
                    stop_reason=resp.stop_reason or "end_turn",
                )

            except (APITimeoutError, APIConnectionError) as exc:
                last_err = exc
                logger.warning("claude.call.retry reason=%s attempt=%d", type(exc).__name__, attempt)
            except APIStatusError as exc:
                last_err = exc
                if exc.status_code >= 500:
                    logger.warning("claude.call.retry reason=5xx status=%d attempt=%d", exc.status_code, attempt)
                else:
                    logger.error("claude.call.4xx status=%d", exc.status_code)
                    if db is not None:
                        db.add(AICall(call_site=call_site, model=model, input_tokens=0, output_tokens=0,
                                      cost_usd=Decimal("0"), latency_ms=0, related_id=related_id,
                                      error_code=f"http_{exc.status_code}"))
                    raise ClaudeUnavailableError(f"Claude {exc.status_code}") from exc
            except APIError as exc:
                last_err = exc
                logger.warning("claude.call.error reason=%s attempt=%d", type(exc).__name__, attempt)

            if attempt < attempts:
                await asyncio.sleep(self._backoff_ms / 1000.0)

        logger.error("claude.call.failed after %d attempts: %s", attempts, last_err)
        if db is not None:
            db.add(AICall(call_site=call_site, model=model, input_tokens=0, output_tokens=0,
                          cost_usd=Decimal("0"), latency_ms=int((time.monotonic() - started) * 1000),
                          related_id=related_id, error_code="exhausted_retries"))
        raise ClaudeUnavailableError(str(last_err))


def _compute_cost(model: str, input_tokens: int, cached_tokens: int, output_tokens: int) -> Decimal:
    pricing = _PRICING.get(model)
    if not pricing:
        return Decimal("0")
    fresh = max(input_tokens - cached_tokens, 0)
    cost = (
        fresh * pricing["input"]
        + cached_tokens * pricing["cached"]
        + output_tokens * pricing["output"]
    ) / 1_000_000
    return Decimal(str(round(cost, 6)))


_singleton: ClaudeClient | None = None


def get_claude() -> ClaudeClient:
    global _singleton
    if _singleton is None:
        _singleton = ClaudeClient()
    return _singleton


def extract_tool_use(content: list[Any], tool_name: str) -> dict[str, Any] | None:
    """Pluck a tool_use block matching name from Claude content array."""
    for block in content:
        if getattr(block, "type", None) == "tool_use" and getattr(block, "name", None) == tool_name:
            return dict(block.input) if block.input else {}
    return None
