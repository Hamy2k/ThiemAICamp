"""Vietnamese accent handling.

Edge case 5 (Phase 1): non-accent input normalized to accented form.
Tested: tests/unit/test_vietnamese.py :: test_accent_normalization
"""
from __future__ import annotations

import unicodedata


def nfc(text: str) -> str:
    """Canonical Unicode composition (NFC) per spec."""
    return unicodedata.normalize("NFC", text)


def strip_accents(text: str) -> str:
    """Remove combining diacritics. Used for fuzzy matching."""
    return "".join(
        ch for ch in unicodedata.normalize("NFD", text) if unicodedata.category(ch) != "Mn"
    ).replace("đ", "d").replace("Đ", "D")


def normalize_for_match(text: str) -> str:
    """Canonical form for gazetteer/landmark lookup: lowercase, no accents, collapsed ws."""
    return " ".join(strip_accents(text).lower().split())


# Minimal landmark → (district, city) mapping for common Saigon/Hanoi/Binh Duong landmarks.
# Expand in production via operational CSV. Only used when LLM also fails.
LANDMARK_MAP: dict[str, tuple[str, str]] = {
    "cho ba chieu": ("Quận Bình Thạnh", "TPHCM"),
    "ba chieu": ("Quận Bình Thạnh", "TPHCM"),
    "binh thanh": ("Quận Bình Thạnh", "TPHCM"),
    "thu duc": ("Thành phố Thủ Đức", "TPHCM"),
    "tan binh": ("Quận Tân Bình", "TPHCM"),
    "tan phu": ("Quận Tân Phú", "TPHCM"),
    "go vap": ("Quận Gò Vấp", "TPHCM"),
    "quan 1": ("Quận 1", "TPHCM"),
    "quan 3": ("Quận 3", "TPHCM"),
    "quan 5": ("Quận 5", "TPHCM"),
    "quan 7": ("Quận 7", "TPHCM"),
    "quan 10": ("Quận 10", "TPHCM"),
    "quan 12": ("Quận 12", "TPHCM"),
    "di an": ("Thành phố Dĩ An", "Bình Dương"),
    "thuan an": ("Thành phố Thuận An", "Bình Dương"),
    "kcn song than": ("Thành phố Dĩ An", "Bình Dương"),
    "ha dong": ("Quận Hà Đông", "Hà Nội"),
    "cau giay": ("Quận Cầu Giấy", "Hà Nội"),
    "long bien": ("Quận Long Biên", "Hà Nội"),
}


def resolve_landmark(area_raw: str) -> tuple[str, str] | None:
    """Resolve a freeform area string (even without tone marks) to (district, city).

    Returns None if no landmark match. Caller falls back to LLM-based normalization.
    """
    canon = normalize_for_match(area_raw)
    if canon in LANDMARK_MAP:
        return LANDMARK_MAP[canon]
    # Substring match on longer keys first (avoid "ba" matching too greedily)
    for key in sorted(LANDMARK_MAP.keys(), key=len, reverse=True):
        if key in canon:
            return LANDMARK_MAP[key]
    return None
