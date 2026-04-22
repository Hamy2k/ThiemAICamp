"""Vietnam district gazetteer with centroids + city-level fallback.

Covers major urban employment hubs. Production should use real geocoding API.
Returns (district, city, lat, lng) or None if no match anywhere.
"""
from __future__ import annotations

from decimal import Decimal

from app.utils.vietnamese import normalize_for_match

# (district, city): (lat, lng)
DISTRICT_CENTROIDS: dict[tuple[str, str], tuple[Decimal, Decimal]] = {
    # TPHCM
    ("Quận 1", "TPHCM"):              (Decimal("10.7769"), Decimal("106.7009")),
    ("Quận 2", "TPHCM"):              (Decimal("10.7872"), Decimal("106.7498")),
    ("Quận 3", "TPHCM"):              (Decimal("10.7794"), Decimal("106.6904")),
    ("Quận 4", "TPHCM"):              (Decimal("10.7578"), Decimal("106.7041")),
    ("Quận 5", "TPHCM"):              (Decimal("10.7540"), Decimal("106.6632")),
    ("Quận 6", "TPHCM"):              (Decimal("10.7467"), Decimal("106.6352")),
    ("Quận 7", "TPHCM"):              (Decimal("10.7337"), Decimal("106.7215")),
    ("Quận 8", "TPHCM"):              (Decimal("10.7404"), Decimal("106.6649")),
    ("Quận 9", "TPHCM"):              (Decimal("10.8428"), Decimal("106.8287")),
    ("Quận 10", "TPHCM"):             (Decimal("10.7674"), Decimal("106.6672")),
    ("Quận 11", "TPHCM"):             (Decimal("10.7629"), Decimal("106.6433")),
    ("Quận 12", "TPHCM"):             (Decimal("10.8631"), Decimal("106.6537")),
    ("Quận Bình Thạnh", "TPHCM"):     (Decimal("10.8106"), Decimal("106.7091")),
    ("Quận Bình Tân", "TPHCM"):       (Decimal("10.7651"), Decimal("106.6036")),
    ("Quận Gò Vấp", "TPHCM"):         (Decimal("10.8381"), Decimal("106.6655")),
    ("Quận Phú Nhuận", "TPHCM"):      (Decimal("10.7975"), Decimal("106.6783")),
    ("Quận Tân Bình", "TPHCM"):       (Decimal("10.8010"), Decimal("106.6526")),
    ("Quận Tân Phú", "TPHCM"):        (Decimal("10.7905"), Decimal("106.6289")),
    ("Thành phố Thủ Đức", "TPHCM"):   (Decimal("10.8231"), Decimal("106.7501")),
    ("Huyện Bình Chánh", "TPHCM"):    (Decimal("10.6956"), Decimal("106.5700")),
    ("Huyện Củ Chi", "TPHCM"):        (Decimal("10.9732"), Decimal("106.4936")),
    ("Huyện Hóc Môn", "TPHCM"):       (Decimal("10.8874"), Decimal("106.5951")),
    ("Huyện Nhà Bè", "TPHCM"):        (Decimal("10.6958"), Decimal("106.7388")),
    # Bình Dương
    ("Thành phố Dĩ An", "Bình Dương"):       (Decimal("10.9042"), Decimal("106.7662")),
    ("Thành phố Thuận An", "Bình Dương"):    (Decimal("10.9190"), Decimal("106.6952")),
    ("Thành phố Thủ Dầu Một", "Bình Dương"): (Decimal("10.9804"), Decimal("106.6519")),
    ("Thị xã Bến Cát", "Bình Dương"):        (Decimal("11.1507"), Decimal("106.6047")),
    ("Thị xã Tân Uyên", "Bình Dương"):       (Decimal("11.0611"), Decimal("106.7878")),
    # Đồng Nai
    ("Thành phố Biên Hòa", "Đồng Nai"):      (Decimal("10.9574"), Decimal("106.8426")),
    ("Thành phố Long Khánh", "Đồng Nai"):    (Decimal("10.9369"), Decimal("107.2388")),
    # Long An
    ("Thành phố Tân An", "Long An"):         (Decimal("10.5329"), Decimal("106.4066")),
    ("Huyện Đức Hòa", "Long An"):            (Decimal("10.8806"), Decimal("106.4193")),
    # Hà Nội
    ("Quận Ba Đình", "Hà Nội"):       (Decimal("21.0378"), Decimal("105.8115")),
    ("Quận Cầu Giấy", "Hà Nội"):      (Decimal("21.0313"), Decimal("105.7892")),
    ("Quận Đống Đa", "Hà Nội"):       (Decimal("21.0187"), Decimal("105.8274")),
    ("Quận Hà Đông", "Hà Nội"):       (Decimal("20.9530"), Decimal("105.7574")),
    ("Quận Hai Bà Trưng", "Hà Nội"):  (Decimal("21.0091"), Decimal("105.8567")),
    ("Quận Hoàn Kiếm", "Hà Nội"):     (Decimal("21.0278"), Decimal("105.8523")),
    ("Quận Hoàng Mai", "Hà Nội"):     (Decimal("20.9730"), Decimal("105.8609")),
    ("Quận Long Biên", "Hà Nội"):     (Decimal("21.0356"), Decimal("105.8933")),
    ("Quận Nam Từ Liêm", "Hà Nội"):   (Decimal("21.0181"), Decimal("105.7656")),
    ("Quận Tây Hồ", "Hà Nội"):        (Decimal("21.0785"), Decimal("105.8260")),
    ("Quận Thanh Xuân", "Hà Nội"):    (Decimal("20.9958"), Decimal("105.8085")),
    # Đà Nẵng
    ("Quận Hải Châu", "Đà Nẵng"):     (Decimal("16.0691"), Decimal("108.2207")),
    ("Quận Liên Chiểu", "Đà Nẵng"):   (Decimal("16.0698"), Decimal("108.1526")),
    ("Quận Sơn Trà", "Đà Nẵng"):      (Decimal("16.1019"), Decimal("108.2437")),
}

# City-level fallback centroids — used when input names a city but no specific district matches.
CITY_FALLBACK: dict[str, tuple[str, Decimal, Decimal]] = {
    "tphcm":    ("Quận 1", Decimal("10.7769"), Decimal("106.7009")),
    "ho chi minh": ("Quận 1", Decimal("10.7769"), Decimal("106.7009")),
    "hcm":      ("Quận 1", Decimal("10.7769"), Decimal("106.7009")),
    "saigon":   ("Quận 1", Decimal("10.7769"), Decimal("106.7009")),
    "sai gon":  ("Quận 1", Decimal("10.7769"), Decimal("106.7009")),
    "ha noi":   ("Quận Hoàn Kiếm", Decimal("21.0278"), Decimal("105.8523")),
    "hanoi":    ("Quận Hoàn Kiếm", Decimal("21.0278"), Decimal("105.8523")),
    "binh duong": ("Thành phố Thủ Dầu Một", Decimal("10.9804"), Decimal("106.6519")),
    "dong nai":   ("Thành phố Biên Hòa", Decimal("10.9574"), Decimal("106.8426")),
    "long an":    ("Thành phố Tân An", Decimal("10.5329"), Decimal("106.4066")),
    "da nang":    ("Quận Hải Châu", Decimal("16.0691"), Decimal("108.2207")),
}

CITY_ALIAS: dict[str, str] = {
    "tphcm": "TPHCM",
    "ho chi minh": "TPHCM",
    "hcm": "TPHCM",
    "saigon": "TPHCM",
    "sai gon": "TPHCM",
    "ha noi": "Hà Nội",
    "hanoi": "Hà Nội",
    "binh duong": "Bình Dương",
    "dong nai": "Đồng Nai",
    "long an": "Long An",
    "da nang": "Đà Nẵng",
}


def get_centroid(district: str, city: str) -> tuple[Decimal, Decimal] | None:
    return DISTRICT_CENTROIDS.get((district, city))


def search_by_fuzzy_name(area_raw: str) -> tuple[str, str, Decimal, Decimal] | None:
    """Best-effort match.

    Strategy (in order):
    1. Substring match on any district name (canonical no-tone form).
    2. City-level fallback: if input mentions a known city name, return that city's default district centroid.
    3. None — caller decides (endpoint returns 400, or use default in seed/demo).
    """
    canon = normalize_for_match(area_raw)

    # 1. District match. Also strip common prefixes ("quan", "huyen", "thanh pho", "thi xa")
    #    so user can type just "thu duc" or "di an" and match.
    PREFIXES = ("thanh pho ", "thi xa ", "quan ", "huyen ")

    def _strip(s: str) -> str:
        for p in PREFIXES:
            if s.startswith(p):
                return s[len(p):]
        return s

    canon_short = _strip(canon)

    candidates: list[tuple[tuple[str, str], tuple[Decimal, Decimal]]] = list(DISTRICT_CENTROIDS.items())
    # Sort by stripped-district-name length, longest first — so "binh thanh" wins over "binh".
    candidates.sort(key=lambda x: len(_strip(normalize_for_match(x[0][0]))), reverse=True)
    for (district, city), (lat, lng) in candidates:
        d_canon = normalize_for_match(district)
        d_short = _strip(d_canon)
        if d_short and (d_short in canon_short or canon_short in d_short):
            return (district, city, lat, lng)

    # 2. City fallback — pick best-known district for that city
    for city_key, (default_district, lat, lng) in CITY_FALLBACK.items():
        if city_key in canon:
            city_name = CITY_ALIAS[city_key]
            return (default_district, city_name, lat, lng)

    return None
