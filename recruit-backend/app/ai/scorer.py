"""Claude Haiku scorer — computes 4 sub-scores, code applies weights.

Fallback: entirely code-based rubric via app.services.scoring.compute_fallback_scores.
"""
from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.client import ClaudeUnavailableError, extract_tool_use, get_claude
from app.ai.prompts import load as load_prompt
from app.config import get_settings
from app.services.scoring import ComponentScores, compute_fallback_scores

logger = logging.getLogger(__name__)


_TOOL_SCHEMA: dict[str, Any] = {
    "name": "emit_score",
    "description": "Emit 4 sub-scores (0-100) and 1 Vietnamese-sentence explanation.",
    "input_schema": {
        "type": "object",
        "required": [
            "score_location",
            "score_availability",
            "score_experience",
            "score_response_quality",
            "explanation_vi",
        ],
        "properties": {
            "score_location":         {"type": "number", "minimum": 0, "maximum": 100},
            "score_availability":     {"type": "number", "minimum": 0, "maximum": 100},
            "score_experience":       {"type": "number", "minimum": 0, "maximum": 100},
            "score_response_quality": {"type": "number", "minimum": 0, "maximum": 100},
            "explanation_vi":         {"type": "string", "maxLength": 220},
        },
    },
}


@dataclass
class ScoringOutput:
    scores: ComponentScores
    explanation_vi: str
    fallback_used: bool


async def score_lead(
    *,
    db: AsyncSession,
    session_id: uuid.UUID,
    distance_km: float | None,
    job_shift: str | None,
    exp_required: bool,
    keywords: list[str],
    extracted: dict[str, Any],
) -> ScoringOutput:
    """Call Claude scorer; fall back to code-only rubric on failure."""
    client = get_claude()
    settings = get_settings()
    system_prompt = load_prompt("scorer")

    user_text = (
        "<job>\n"
        f"shift: {job_shift}\n"
        f"exp_required: {exp_required}\n"
        f"keywords: {keywords}\n"
        "</job>\n\n"
        "<candidate>\n"
        f"distance_km: {distance_km}\n"
        f"extracted: {extracted}\n"
        f"fields_captured: {_captured_count(extracted)}/4\n"
        "</candidate>\n\n"
        "Gọi emit_score."
    )

    try:
        result = await client.call(
            model=settings.model_scoring,
            system=system_prompt,
            messages=[{"role": "user", "content": user_text}],
            tools=[_TOOL_SCHEMA],
            tool_choice={"type": "tool", "name": "emit_score"},
            max_tokens=400,
            call_site="scoring",
            related_id=session_id,
            db=db,
        )
        payload = extract_tool_use(result.content, "emit_score")
        if not payload:
            raise ClaudeUnavailableError("emit_score not returned")
        scores = ComponentScores(
            location=Decimal(str(payload["score_location"])),
            availability=Decimal(str(payload["score_availability"])),
            experience=Decimal(str(payload["score_experience"])),
            response_quality=Decimal(str(payload["score_response_quality"])),
        )
        return ScoringOutput(
            scores=scores,
            explanation_vi=payload["explanation_vi"],
            fallback_used=False,
        )
    except (ClaudeUnavailableError, KeyError, ValueError, TypeError) as exc:
        logger.warning("scorer.fallback session_id=%s reason=%s", session_id, exc)
        scores = compute_fallback_scores(
            distance_km=distance_km,
            job_shift=job_shift,
            exp_required=exp_required,
            keywords=keywords,
            extracted=extracted,
        )
        return ScoringOutput(
            scores=scores,
            explanation_vi="Hệ thống đánh giá dựa trên quy tắc cơ bản. Nhà tuyển dụng sẽ xem lại.",
            fallback_used=True,
        )


def _captured_count(extracted: dict[str, Any]) -> int:
    count = 0
    for f in ("start_date", "shift_availability", "experience", "questions_from_candidate"):
        if extracted.get(f) not in (None, {}, []):
            count += 1
    return count
