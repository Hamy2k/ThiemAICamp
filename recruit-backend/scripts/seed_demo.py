"""Seed demo data for local demo — no Claude API key needed.

Creates: 1 company + 1 HR + 1 active job + 1 content variant + 1 source + 1 tracking_link.
Prints the tracking_id — use in /apply?tracking_id=<id>.
"""
from __future__ import annotations

import asyncio
import os
import sys
from decimal import Decimal

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.session import AsyncSessionLocal  # noqa: E402
from app.db.models import (  # noqa: E402
    Company,
    ContentVariant,
    HRUser,
    Job,
    Source,
    TrackingLink,
)

TRACKING_ID = "demo123abc"
HR_TOKEN = "demo-hr-token"

SAMPLE_COPY = """🔥 TUYỂN GẤP 20 CÔNG NHÂN ÉP NHỰA 🔥

📍 KCN Sóng Thần, Dĩ An, Bình Dương
💰 Lương 8-10 triệu + tăng ca
🕘 Ca xoay, nhận cả người chưa có kinh nghiệm
📅 Bắt đầu 05/05

👉 Đăng ký 30s tại: {link}

#vieclam #dian #binhduong"""


async def main() -> None:
    async with AsyncSessionLocal() as s:
        # Company
        c = Company(name="ABC Plastics (Demo)", industry="manufacturing")
        s.add(c)
        await s.flush()

        # HR user
        hr = HRUser(
            company_id=c.id,
            email="hr@abc.demo",
            full_name="HR Demo",
            api_key_hash=HR_TOKEN,
            telegram_chat_id=None,
        )
        s.add(hr)
        await s.flush()

        # Active job
        job = Job(
            company_id=c.id,
            created_by=hr.id,
            title="Công nhân vận hành máy ép nhựa",
            salary_text="8-10 triệu + tăng ca",
            salary_min_vnd=8_000_000,
            salary_max_vnd=10_000_000,
            location_raw="KCN Sóng Thần, Dĩ An, Bình Dương",
            location_district="Thành phố Dĩ An",
            location_city="Bình Dương",
            location_lat=Decimal("10.9042"),
            location_lng=Decimal("106.7662"),
            shift="rotating",
            requirements_raw="Nam/nữ 18-35t, không cần kinh nghiệm, đi làm ca đêm được",
            requirements_parsed={
                "exp_required": False,
                "age_min": 18,
                "age_max": 35,
                "keywords": ["ca đêm", "ép nhựa", "vận hành máy"],
            },
            target_hires=20,
            status="active",
        )
        s.add(job)
        await s.flush()

        # Content variant (manual — skips Claude Sonnet)
        variant = ContentVariant(
            job_id=job.id,
            variant_index=1,
            hook_style="urgency",
            copy_vietnamese=SAMPLE_COPY,
            generated_by_model="manual-seed",
            token_usage={"input": 0, "output": 0, "cost_usd": 0, "source": "seed"},
        )
        s.add(variant)
        await s.flush()

        # Source (Facebook group)
        src = Source(
            channel="facebook",
            external_id="demo-vieclam-tphcm",
            display_name="Việc làm TPHCM (demo)",
        )
        s.add(src)
        await s.flush()

        # Tracking link — fixed ID for easy demo URL
        tlink = TrackingLink(
            tracking_id=TRACKING_ID,
            job_id=job.id,
            variant_id=variant.id,
            source_id=src.id,
            created_by=hr.id,
        )
        s.add(tlink)
        await s.commit()

        print()
        print("=" * 60)
        print("  DEMO DATA SEEDED")
        print("=" * 60)
        print(f"Job title      : {job.title}")
        print(f"Location       : {job.location_district}, {job.location_city}")
        print(f"Tracking ID    : {TRACKING_ID}")
        print(f"HR Bearer token: {HR_TOKEN}")
        print()
        print("Landing URL (replace host with your LAN IP for phone test):")
        print(f"  http://localhost:3000/apply?tracking_id={TRACKING_ID}")
        print()


if __name__ == "__main__":
    asyncio.run(main())
