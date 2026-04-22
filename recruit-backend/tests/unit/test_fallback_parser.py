"""Rule-based fallback parser tests (used when Claude fails)."""
from __future__ import annotations

from app.ai.fallback_parser import parse_message_fallback


def test_hours_extracted() -> None:
    assert parse_message_fallback("lamj dc 8h")["hours_per_day"] == 8
    assert parse_message_fallback("làm được 10 tiếng")["hours_per_day"] == 10


def test_no_experience_willing() -> None:
    out = parse_message_fallback("kh co kinh nghiem nhug chiuj hoc")
    assert out["experience"]["has_experience"] is False
    assert out["experience"]["willing_to_learn"] is True


def test_night_shift_not_preferred() -> None:
    out = parse_message_fallback("lam dc ca dem nhung k thich")
    sa = out["shift_availability"]
    assert sa["night"] is True
    # Preferred is NOT night when user dislikes
    assert sa["preferred"] != "night"


def test_proximity_flag() -> None:
    assert parse_message_fallback("muon lam gan nha")["prefers_proximity"] is True


def test_start_date_next_week() -> None:
    assert parse_message_fallback("em ranh tu tuan sau")["start_date"] == "next_week"


def test_landmark_resolved() -> None:
    out = parse_message_fallback("em o gan cho ba chieu")
    assert out["normalized_location"] == {"district": "Quận Bình Thạnh", "city": "TPHCM"}
