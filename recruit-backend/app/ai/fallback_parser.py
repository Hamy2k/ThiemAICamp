"""Rule-based fallback parser — used when Claude fails twice.

Edge case 5 (non-accent Vietnamese) partially handled here.
Tested: tests/unit/test_fallback_parser.py + test_edge_cases.py :: test_accent_normalization
"""
from __future__ import annotations

import re
from typing import Any

from app.utils.vietnamese import normalize_for_match, resolve_landmark


_HOURS_RE = re.compile(r"(\d{1,2})\s*(?:h|giờ|tieng|tiếng)", re.IGNORECASE)
_NIGHT_KEYWORDS = ("dem", "đêm", "toi", "tối", "night")
_DAY_KEYWORDS = ("ngay", "ngày", "day", "sang", "sáng", "chieu", "chiều")
_ROTATING_KEYWORDS = ("xoay", "ca xoay", "luân phiên", "rotating")
_EXPERIENCE_YES = ("co kinh nghiem", "có kinh nghiệm", "lam lau", "làm lâu", "da lam", "đã làm")
_EXPERIENCE_NO = (
    "khong co kinh nghiem", "không có kinh nghiệm",
    "chua co kinh nghiem", "chưa có kinh nghiệm",
    "k co kn", "kh co kinh nghiem",
)
_WILLING = ("chiu hoc", "chịu học", "sang hoc", "sẵn sàng học", "muon hoc", "muốn học")
_PROXIMITY = ("gan nha", "gần nhà", "gan cong ty", "gần công ty")
_NEXT_WEEK = ("tuan sau", "tuần sau", "next week")
_NEXT_MONTH = ("thang sau", "tháng sau", "next month")
_ASAP = ("luon", "ngay", "ngay lập tức", "asap", "di lien", "đi liền")


def parse_message_fallback(text: str) -> dict[str, Any]:
    """Extract partial structured data from a raw message using regex + keyword rules.

    Returns an `extracted_delta` shape matching screening.ExtractedDelta.
    Never raises — always returns best-effort dict.
    """
    canon = normalize_for_match(text)
    out: dict[str, Any] = {}

    # hours
    m = _HOURS_RE.search(text)
    if m:
        try:
            h = int(m.group(1))
            if 1 <= h <= 24:
                out["hours_per_day"] = h
        except ValueError:
            pass

    # shift
    night = any(k in canon for k in _NIGHT_KEYWORDS)
    day = any(k in canon for k in _DAY_KEYWORDS)
    rotating = any(k in canon for k in _ROTATING_KEYWORDS)
    disliked = " k thich" in canon or "khong thich" in canon or "k thich" in canon
    if night or day or rotating:
        preferred: str | None = None
        if night and not disliked:
            preferred = "night"
        elif day and not night:
            preferred = "day"
        elif rotating:
            preferred = "rotating"
        out["shift_availability"] = {
            "day": True if day else None,
            "night": True if night else None,
            "rotating": True if rotating else None,
            "preferred": preferred if preferred else ("day" if disliked and night else None),
        }

    # experience
    exp: dict[str, Any] = {}
    if any(k in canon for k in _EXPERIENCE_NO):
        exp["has_experience"] = False
    elif any(k in canon for k in _EXPERIENCE_YES):
        exp["has_experience"] = True
    if any(k in canon for k in _WILLING):
        exp["willing_to_learn"] = True
    if exp:
        out["experience"] = exp

    # start_date
    if any(k in canon for k in _NEXT_WEEK):
        out["start_date"] = "next_week"
    elif any(k in canon for k in _NEXT_MONTH):
        out["start_date"] = "next_month"
    elif any(k in canon for k in _ASAP):
        out["start_date"] = "asap"

    # proximity
    if any(k in canon for k in _PROXIMITY):
        out["prefers_proximity"] = True

    # location from landmark
    landmark = resolve_landmark(text)
    if landmark:
        d, c = landmark
        out["normalized_location"] = {"district": d, "city": c}

    return out
