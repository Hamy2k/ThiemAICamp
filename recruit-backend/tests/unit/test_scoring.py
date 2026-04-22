"""Deterministic scoring rubric tests."""
from __future__ import annotations

from decimal import Decimal

import pytest

from app.schemas.screening import ExperienceInfo, ExtractedDelta, ShiftAvailability
from app.services.scoring import (
    compute_fallback_scores,
    compute_tier,
    score_availability_rule,
    score_experience_rule,
    score_location_from_km,
    score_response_quality,
)


@pytest.mark.parametrize(
    "km,expected",
    [(0, 100), (4.9, 100), (5, 100), (7, 70), (15, 70), (20, 40), (35, 10), (None, 50)],
)
def test_location_score(km: float | None, expected: int) -> None:
    assert score_location_from_km(km) == Decimal(str(expected))


def test_availability_exact_match() -> None:
    delta = ExtractedDelta(shift_availability=ShiftAvailability(night=True, preferred="night"))
    assert score_availability_rule("night", delta) == Decimal("100")


def test_availability_match_but_not_preferred() -> None:
    delta = ExtractedDelta(shift_availability=ShiftAvailability(night=True, preferred="day"))
    assert score_availability_rule("night", delta) == Decimal("50")


def test_availability_mismatch() -> None:
    delta = ExtractedDelta(shift_availability=ShiftAvailability(day=True, preferred="day"))
    assert score_availability_rule("night", delta) == Decimal("0")


def test_availability_missing_data() -> None:
    assert score_availability_rule("day", ExtractedDelta()) == Decimal("40")


def test_experience_keyword_match() -> None:
    delta = ExtractedDelta(experience=ExperienceInfo(has_experience=True, related_keywords=["ép nhựa"]))
    # exp_required=True → base=100
    assert score_experience_rule(True, ["ép nhựa"], delta) == Decimal("100")


def test_experience_none_willing_not_required() -> None:
    delta = ExtractedDelta(experience=ExperienceInfo(has_experience=False, willing_to_learn=True))
    # base=40, +20 because exp_required=False → 60
    assert score_experience_rule(False, [], delta) == Decimal("60")


def test_response_quality() -> None:
    assert score_response_quality({"start_date": "asap", "shift_availability": {"day": True},
                                    "experience": {"has_experience": False},
                                    "questions_from_candidate": []}) == Decimal("100")
    # questions_from_candidate is empty list — treated as missing per rubric comment
    assert score_response_quality({"start_date": "asap"}) == Decimal("20")


def test_tier_boundaries() -> None:
    assert compute_tier(Decimal("70")) == "hot"
    assert compute_tier(Decimal("69.99")) == "warm"
    assert compute_tier(Decimal("40")) == "warm"
    assert compute_tier(Decimal("39")) == "cold"


def test_fallback_full_computation() -> None:
    scores = compute_fallback_scores(
        distance_km=8.0,
        job_shift="rotating",
        exp_required=False,
        keywords=["ép nhựa"],
        extracted={
            "start_date": "asap",
            "shift_availability": {"rotating": True, "preferred": "rotating"},
            "experience": {"has_experience": False, "willing_to_learn": True},
            "questions_from_candidate": [],
        },
    )
    assert scores.location == Decimal("70")
    assert scores.availability == Decimal("100")
    assert scores.experience == Decimal("60")  # 40 + 20 (exp not required)
    total = scores.total()
    # 70*0.4 + 100*0.3 + 60*0.2 + 100*0.1 = 28 + 30 + 12 + 10 = 80
    assert total == Decimal("80.00")
