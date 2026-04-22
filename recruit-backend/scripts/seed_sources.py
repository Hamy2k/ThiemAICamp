"""Add 2 extra sources so share-kit has multiple cards for demo."""
from __future__ import annotations

import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select  # noqa: E402

from app.db.session import AsyncSessionLocal  # noqa: E402
from app.db.models import Source  # noqa: E402


EXTRA_SOURCES = [
    ("facebook", "demo-vieclam-binh-duong", "Việc làm Bình Dương (demo)"),
    ("zalo",     "demo-zalo-forward",       "Zalo forward A (demo)"),
]


async def main() -> None:
    async with AsyncSessionLocal() as s:
        for channel, ext_id, display in EXTRA_SOURCES:
            existing = await s.execute(
                select(Source).where(Source.channel == channel, Source.external_id == ext_id)
            )
            if existing.scalar_one_or_none():
                continue
            s.add(Source(channel=channel, external_id=ext_id, display_name=display))
        await s.commit()
    print("extra sources ready")


if __name__ == "__main__":
    asyncio.run(main())
