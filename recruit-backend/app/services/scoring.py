"""Deterministic scoring rubric from Phase 1 spec.

Weights: location 40%, availability 30%, experience 20%, response_quality 10%.
Code applies weights; LLM computes sub-scores (via app.ai.scorer).
Fallback: code-only deterministic calculation when LLM fails.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Literal

from app.schemas.screening import ExtractedDelta

Tier = Literal["hot", "warm", "cold"]

WEIGHT_LOCATION = Decimal("0.40")
WEIGHT_AVAILABILITY = Decimal("0.30")
WEIGHT_EXPERIENCE = Decimal("0.20")
WEIGHT_RESPONSE_QUALITY = Decimal("0.10")


@dataclass
class ComponentScores:
    location: Decimal
    availability: Decimal
    experience: Decimal
    response_quality: Decimal

    def total(self) -> Decimal:
        return (
            self.location * WEIGHT_LOCATION
            + self.availability * WEIGHT_AVAILABILITY
            + self.experience * WEIGHT_EXPERIENCE
            + self.response_quality * WEIGHT_RESPONSE_QUALITY
        ).quantize(Decimal("0.01"))


def compute_tier(total: Decimal) -> Tier:
    if total >= Decimal("70"):
        return "hot"
    if total >= Decimal("40"):
        return "warm"
    return "cold"


def haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Great-circle distance in km."""
    r = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lng2 - lng1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def score_location_from_km(distance_km: float | None) -> Decimal:
    if distance_km is None:
        return Decimal("50")
    if distance_km <= 5:
        return Decimal("100")
    if distance_km <= 15:
        return Decimal("70")
    if distance_km <= 30:
        return Decimal("40")
    return Decimal("10")


def score_availability_rule(
    job_shift: str | None,
    candidate: ExtractedDelta,
) -> Decimal:
    """Deterministic availability rubric (Phase 1 §4.3 rubric 2)."""
    sa = candidate.shift_availability
    if not sa or not job_shift:
        return Decimal("40")
    matches = {
        "day": sa.day,
        "night": sa.night,
        "rotating": sa.rotating,
    }
    if job_shift == "flexible":
        if any(matches.values()):
            return Decimal("100")
        return Decimal("10")
    if matches.get(job_shift) is True:
        if sa.preferred in (job_shift, "any", None):
            return Decimal("100")
        return Decimal("50")
    return Decimal("0")


def score_experience_rule(
    exp_required: bool,
    keywords: list[str],
    candidate: ExtractedDelta,
) -> Decimal:
    """Deterministic experience rubric (Phase 1 §4.3 rubric 3)."""
    exp = candidate.experience
    base: Decimal
    if exp is None:
        base = Decimal("20")
    elif exp.has_experience:
        cand_kw_lower = [k.lower() for k in exp.related_keywords]
        if any(kw.lower() in cand_kw_lower for kw in keywords):
            base = Decimal("100")
        else:
            base = Decimal("60")
    else:
        base = Decimal("40") if exp.willing_to_learn else Decimal("0")
    if not exp_required:
        base = min(base + Decimal("20"), Decimal("100"))
    return base


def score_response_quality(extracted: dict[str, Any]) -> Decimal:
    """Completeness of 4 required fields (Phase 1 §4.3 rubric 4)."""
    required_fields = ("start_date", "shift_availability", "experience", "questions_from_candidate")
    got = sum(1 for f in required_fields if extracted.get(f) not in (None, {}, []))
    if got == 4:
        return Decimal("100")
    if got == 3:
        return Decimal("80")
    if got == 2:
        return Decimal("50")
    return Decimal("20")


def compute_fallback_scores(
    *,
    distance_km: float | None,
    job_shift: str | None,
    exp_required: bool,
    keywords: list[str],
    extracted: dict[str, Any],
) -> ComponentScores:
    """Compute all 4 sub-scores entirely in code. Used when Claude scorer fails twice."""
    delta = ExtractedDelta.model_validate(extracted)
    return ComponentScores(
        location=score_location_from_km(distance_km),
        availability=score_availability_rule(job_shift, delta),
        experience=score_experience_rule(exp_required, keywords, delta),
        response_quality=score_response_quality(extracted),
    )
