"""Phone E.164 normalization.

Edge case 6 (Phase 1): handles `0909…`, `+8490…`, `84 909…`, `84-909…`.
Tested: tests/unit/test_phone.py :: test_phone_normalization_e164
"""
from __future__ import annotations

import re

import phonenumbers
from phonenumbers import NumberParseException

_VN_DEFAULT_REGION = "VN"


class InvalidPhoneError(ValueError):
    """Raised when input cannot be parsed as a valid Vietnamese phone."""


def normalize_phone_e164(raw: str) -> str:
    """Convert any common VN phone format to E.164 (+84...).

    Accepts:
      - 0909123456
      - +84909123456
      - 84 909 123 456
      - 84-909-123-456
      - (+84) 909.123.456

    Returns E.164 string like '+84909123456'.
    Raises InvalidPhoneError on unparseable input.
    """
    if not raw or not raw.strip():
        raise InvalidPhoneError("Phone is empty")

    cleaned = re.sub(r"[\s\-.()]+", "", raw.strip())

    # Handle "84..." without + prefix (treat as E.164 intent)
    if cleaned.startswith("84") and not cleaned.startswith("+84") and len(cleaned) >= 10:
        cleaned = "+" + cleaned

    try:
        number = phonenumbers.parse(cleaned, _VN_DEFAULT_REGION)
    except NumberParseException as exc:
        raise InvalidPhoneError(f"Unparseable phone: {raw}") from exc

    if not phonenumbers.is_valid_number(number):
        raise InvalidPhoneError(f"Invalid phone number: {raw}")

    return phonenumbers.format_number(number, phonenumbers.PhoneNumberFormat.E164)


def mask_phone(phone_e164: str) -> str:
    """Display-safe masked phone: '+84909***456' for HR-facing lists."""
    if len(phone_e164) < 7:
        return phone_e164
    return phone_e164[:5] + "***" + phone_e164[-4:]
