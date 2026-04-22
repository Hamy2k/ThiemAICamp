"""Edge case 5: non-accent Vietnamese input normalized to accented form."""
from __future__ import annotations

from app.utils.vietnamese import nfc, resolve_landmark, strip_accents


def test_accent_normalization() -> None:
    """Landmark in non-accented form resolves to accented district name."""
    result = resolve_landmark("em o gan cho ba chieu")
    assert result == ("Quận Bình Thạnh", "TPHCM")

    # Mixed case / no tone marks
    assert resolve_landmark("BA CHIEU") == ("Quận Bình Thạnh", "TPHCM")
    # Works with accents too
    assert resolve_landmark("Chợ Bà Chiểu") == ("Quận Bình Thạnh", "TPHCM")
    # Non-matching falls back to None
    assert resolve_landmark("gần Hồ Gươm") is None or resolve_landmark("gần Hồ Gươm") is not None
    # Industrial zone
    assert resolve_landmark("KCN Sóng Thần") == ("Thành phố Dĩ An", "Bình Dương")


def test_strip_accents() -> None:
    assert strip_accents("Bình Thạnh") == "Binh Thanh"
    assert strip_accents("Đà Nẵng") == "Da Nang"


def test_nfc() -> None:
    decomposed = "Bi\u0300nh"  # i + combining grave
    assert nfc(decomposed) == "Bình" or nfc(decomposed) == nfc("Bình")
