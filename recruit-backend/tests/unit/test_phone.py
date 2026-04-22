"""Edge case 6: phone format normalization to E.164."""
from __future__ import annotations

import pytest

from app.utils.phone import InvalidPhoneError, mask_phone, normalize_phone_e164


@pytest.mark.parametrize(
    "raw",
    [
        "0909123456",
        "+84909123456",
        "84909123456",
        "84 909 123 456",
        "84-909-123-456",
        "(+84) 909.123.456",
        " 0909 123.456 ",
    ],
)
def test_phone_normalization_e164(raw: str) -> None:
    """Every valid VN phone format → +84909123456."""
    assert normalize_phone_e164(raw) == "+84909123456"


@pytest.mark.parametrize("raw", ["", "   ", "abc", "12345", "+1"])
def test_phone_normalization_rejects_invalid(raw: str) -> None:
    with pytest.raises(InvalidPhoneError):
        normalize_phone_e164(raw)


def test_mask_phone_hides_middle() -> None:
    assert mask_phone("+84909123456") == "+8490***3456"
