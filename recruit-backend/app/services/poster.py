"""Generate Facebook-ready job posters (1200x630 PNG).

Server-rendered with Pillow — no external image API, no cost, no quota.
Vietnamese text uses fallback font chain: Arial → DejaVu Sans.
"""
from __future__ import annotations

import logging
import math
import os
import uuid
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

logger = logging.getLogger(__name__)

POSTERS_DIR = Path(__file__).resolve().parent.parent.parent / "public" / "posters"
POSTERS_DIR.mkdir(parents=True, exist_ok=True)

# Palette — red/orange dominant for urgency (blue-collar Vietnamese market responds strongly to these)
PALETTES = [
    # (top-left bg, bottom-right bg, accent yellow, dark text)
    ((220, 38, 38), (127, 29, 29), (252, 211, 77), (20, 20, 20)),   # red dominant
    ((234, 88, 12), (154, 52, 18), (254, 240, 138), (20, 20, 20)),  # orange
    ((22, 163, 74), (21, 94, 58), (253, 224, 71), (20, 20, 20)),    # green (money vibe)
    ((30, 64, 175), (30, 58, 138), (250, 204, 21), (20, 20, 20)),   # deep blue
    ((190, 24, 93), (131, 24, 67), (253, 224, 71), (20, 20, 20)),   # magenta (new)
]

FONT_CANDIDATES = [
    "C:/Windows/Fonts/arialbd.ttf",
    "C:/Windows/Fonts/arial.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/System/Library/Fonts/Helvetica.ttc",
]


def _load_font(size: int) -> ImageFont.FreeTypeFont:
    for path in FONT_CANDIDATES:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size=size)
            except Exception:  # noqa: BLE001
                continue
    return ImageFont.load_default()


def _gradient_bg(width: int, height: int, top: tuple[int, int, int], bottom: tuple[int, int, int]) -> Image.Image:
    """Diagonal gradient for dynamism (not flat vertical)."""
    img = Image.new("RGB", (width, height), top)
    draw = ImageDraw.Draw(img)
    # Vertical component
    for y in range(height):
        t = y / max(1, height - 1)
        r = int(top[0] + (bottom[0] - top[0]) * t)
        g = int(top[1] + (bottom[1] - top[1]) * t)
        b = int(top[2] + (bottom[2] - top[2]) * t)
        draw.line([(0, y), (width, y)], fill=(r, g, b))
    return img


def _add_diagonal_rays(img: Image.Image) -> None:
    """Subtle diagonal light rays at low opacity — adds visual energy."""
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay, "RGBA")
    W, H = img.size
    for i in range(-8, 8):
        offset = i * 180
        d.polygon(
            [
                (offset, 0),
                (offset + 80, 0),
                (offset + 80 + H, H),
                (offset + H, H),
            ],
            fill=(255, 255, 255, 12),
        )
    img.paste(overlay, (0, 0), overlay)


def _wrap_text(text: str, font: ImageFont.FreeTypeFont, max_width: int, draw: ImageDraw.ImageDraw) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current = ""
    for w in words:
        trial = f"{current} {w}".strip()
        bbox = draw.textbbox((0, 0), trial, font=font)
        if bbox[2] - bbox[0] <= max_width:
            current = trial
        else:
            if current:
                lines.append(current)
            current = w
    if current:
        lines.append(current)
    return lines


def _draw_corner_ribbon(draw: ImageDraw.ImageDraw, text: str, color: tuple[int, int, int]) -> None:
    """Top-right diagonal ribbon with urgency text — eye catcher."""
    # Rotated strip at top-right corner
    pts = [(1000, 0), (1200, 0), (1200, 200), (1040, 200)]  # parallelogram
    draw.polygon(pts, fill=color)
    # Diagonal text on the ribbon — pre-render to rotated image
    font = _load_font(32)
    text_img = Image.new("RGBA", (300, 60), (0, 0, 0, 0))
    td = ImageDraw.Draw(text_img)
    td.text((10, 10), text, fill="white", font=font)
    rotated = text_img.rotate(-45, expand=True, resample=Image.Resampling.BICUBIC)
    # Paste rotated text onto ribbon area (approximate)
    base_img = draw._image  # type: ignore[attr-defined]
    base_img.paste(rotated, (1010, 50), rotated)


def generate_poster(
    *,
    job_id: uuid.UUID,
    title: str,
    salary_text: str | None,
    location_district: str,
    location_city: str,
    target_hires: int,
    company_name: str | None = None,
) -> str:
    """Render a 1200x630 poster and return its public URL path."""
    W, H = 1200, 630
    palette_idx = abs(hash(str(job_id))) % len(PALETTES)
    top_color, bottom_color, accent, dark_text = PALETTES[palette_idx]

    img = _gradient_bg(W, H, top_color, bottom_color)
    _add_diagonal_rays(img)
    draw = ImageDraw.Draw(img, "RGBA")

    # ── Top-left HOT badge pill ───────────────────────────────────────
    badge_text = f"TUYỂN GẤP  •  {target_hires} NGƯỜI"
    badge_font = _load_font(30)
    bbox = draw.textbbox((0, 0), badge_text, font=badge_font)
    badge_w = bbox[2] - bbox[0] + 48
    badge_h = bbox[3] - bbox[1] + 26
    draw.rounded_rectangle(
        [(50, 50), (50 + badge_w, 50 + badge_h)],
        radius=badge_h // 2, fill=accent,
    )
    draw.text((74, 58), badge_text, fill=dark_text, font=badge_font)

    # ── Corner triangle (top-right for visual weight) ────────────────
    draw.polygon(
        [(W, 0), (W, 160), (W - 160, 0)],
        fill=(255, 255, 255, 40),
    )

    # ── Title (centered horizontally) ────────────────────────────────
    title_font = _load_font(74)
    title_display = title.upper()
    title_lines = _wrap_text(title_display, title_font, W - 140, draw)[:2]
    y = 175
    for line in title_lines:
        lb = draw.textbbox((0, 0), line, font=title_font)
        line_w = lb[2] - lb[0]
        # Shadow for depth
        draw.text(((W - line_w) // 2 + 3, y + 3), line, fill=(0, 0, 0, 80), font=title_font)
        draw.text(((W - line_w) // 2, y), line, fill="white", font=title_font)
        y += 86

    y += 10

    # ── Salary BIG BOX (accent yellow, dark text — max contrast) ─────
    if salary_text:
        salary_font = _load_font(78)
        salary_label_font = _load_font(22)

        sb = draw.textbbox((0, 0), salary_text.upper(), font=salary_font)
        sw = sb[2] - sb[0]
        box_padding_x = 60
        box_w = sw + box_padding_x * 2
        box_w = min(box_w, W - 140)
        box_h = 110
        box_x = (W - box_w) // 2
        box_y = y

        # Drop shadow
        draw.rounded_rectangle(
            [(box_x + 4, box_y + 4), (box_x + box_w + 4, box_y + box_h + 4)],
            radius=16, fill=(0, 0, 0, 90),
        )
        # Yellow box
        draw.rounded_rectangle(
            [(box_x, box_y), (box_x + box_w, box_y + box_h)],
            radius=16, fill=accent,
        )
        # Label
        draw.text(
            (box_x + 20, box_y + 10),
            "LƯƠNG", fill=dark_text, font=salary_label_font,
        )
        # Value
        draw.text(
            (box_x + (box_w - sw) // 2, box_y + 30),
            salary_text.upper(), fill=dark_text, font=salary_font,
        )
        y = box_y + box_h + 20

    # ── Bottom panel (company + location + CTA) ──────────────────────
    panel_h = 140
    draw.rectangle([(0, H - panel_h), (W, H)], fill=(0, 0, 0, 140))

    # Company + location — left side
    loc_label_font = _load_font(20)
    company_font = _load_font(32)
    loc_font = _load_font(24)

    ly = H - panel_h + 20
    draw.text((50, ly), "ĐỊA ĐIỂM LÀM VIỆC", fill=(255, 255, 255, 180), font=loc_label_font)
    ly += 28
    if company_name:
        # Strip "(Demo)" or trailing parens for visual cleanliness
        display_company = company_name.split("(")[0].strip() or company_name
        draw.text((50, ly), display_company, fill="white", font=company_font)
        ly += 40
        draw.text(
            (50, ly),
            f"{location_district}, {location_city}",
            fill=(255, 255, 255, 220), font=loc_font,
        )
    else:
        draw.text((50, ly), f"{location_district}, {location_city}", fill="white", font=company_font)

    # CTA — right side, big yellow pill
    cta_font = _load_font(32)
    cta_text = "ĐĂNG KÝ NGAY  >>"
    cbox = draw.textbbox((0, 0), cta_text, font=cta_font)
    cta_w = cbox[2] - cbox[0]
    pill_pad = 32
    pill_right = W - 50
    pill_left = pill_right - cta_w - pill_pad * 2
    pill_top = H - panel_h + 38
    pill_bottom = H - 32
    # Shadow
    draw.rounded_rectangle(
        [(pill_left + 3, pill_top + 3), (pill_right + 3, pill_bottom + 3)],
        radius=(pill_bottom - pill_top) // 2, fill=(0, 0, 0, 120),
    )
    draw.rounded_rectangle(
        [(pill_left, pill_top), (pill_right, pill_bottom)],
        radius=(pill_bottom - pill_top) // 2, fill=accent,
    )
    text_y = pill_top + (pill_bottom - pill_top - (cbox[3] - cbox[1])) // 2 - 4
    draw.text((pill_left + pill_pad, text_y), cta_text, fill=dark_text, font=cta_font)

    # Save
    filename = f"{job_id}.png"
    out_path = POSTERS_DIR / filename
    img.save(out_path, "PNG", optimize=True)
    logger.info("poster.generated job_id=%s path=%s", job_id, out_path)

    return f"/posters/{filename}"
