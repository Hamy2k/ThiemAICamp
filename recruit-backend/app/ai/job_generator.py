"""Claude Sonnet job post generator — 1 high-quality variant per call (Option X)."""
from __future__ import annotations

import logging
import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.client import ClaudeUnavailableError, extract_tool_use, get_claude
from app.ai.prompts import load as load_prompt
from app.config import get_settings

logger = logging.getLogger(__name__)


_TOOL_SCHEMA: dict[str, Any] = {
    "name": "emit_variants",
    "description": "Emit 1 high-quality Facebook-ready Vietnamese job post.",
    "input_schema": {
        "type": "object",
        "required": ["variants", "warnings"],
        "properties": {
            "variants": {
                "type": "array", "minItems": 1, "maxItems": 1,
                "items": {
                    "type": "object",
                    "required": ["hook_style", "copy_vietnamese"],
                    "properties": {
                        "hook_style": {"enum": ["urgency","salary_first","proximity","friendly","detailed"]},
                        "copy_vietnamese": {"type": "string", "minLength": 140, "maxLength": 340},
                    },
                },
            },
            "warnings": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["code", "message"],
                    "properties": {
                        "code": {"enum": ["SALARY_BELOW_MARKET", "VAGUE_LOCATION", "UNREALISTIC_REQUIREMENT"]},
                        "message": {"type": "string"},
                    },
                },
            },
        },
    },
}


def _stub_variants(
    *,
    title: str,
    salary_text: str | None,
    location_district: str,
    location_city: str,
    target_hires: int,
    company_name: str | None = None,
) -> dict[str, Any]:
    """Demo-mode fallback when ANTHROPIC_API_KEY is empty.

    Returns exactly 1 plausible VN variant (urgency hook). Production must set
    ANTHROPIC_API_KEY so Claude Sonnet generates real content.
    """
    loc_with_company = (
        f"{company_name.split('(')[0].strip()}, {location_district}, {location_city}"
        if company_name else f"{location_district}, {location_city}"
    )
    salary = salary_text or "Thương lượng"
    hashtag_suffix = location_district.split()[-1].lower()
    copy = (
        f"🔥 TUYỂN GẤP {target_hires} {title.upper()}\n"
        f"💰 {salary}\n"
        f"👉 Đăng ký 30s: {{link}}\n"
        f"\n"
        f"📍 {loc_with_company}\n"
        f"🕘 Ca linh hoạt, nhận cả người chưa kinh nghiệm\n"
        f"✅ Đi làm đúng giờ là được\n"
        f"\n"
        f"#vieclam #{hashtag_suffix} #tuyendung"
    )
    return {
        "variants": [{"hook_style": "urgency", "copy_vietnamese": copy}],
        "warnings": [],
        "token_usage": {"input": 0, "output": 0, "cost_usd": 0, "source": "stub-no-api-key"},
    }


async def generate_variants(
    *,
    db: AsyncSession,
    job_id: uuid.UUID,
    title: str,
    salary_text: str | None,
    location_district: str,
    location_city: str,
    shift: str | None,
    start_date: str | None,
    requirements_raw: str | None,
    target_hires: int,
    company_name: str | None = None,
) -> dict[str, Any]:
    """Return {variants:list, warnings:list, token_usage:dict}. Raises ClaudeUnavailableError.

    Demo-mode: if ANTHROPIC_API_KEY is empty/missing, returns stub variants
    instead of calling Claude. Logged via token_usage.source = 'stub-no-api-key'.
    """
    settings = get_settings()
    if not settings.anthropic_api_key:
        logger.info("job_post_gen.stub reason=no_api_key job_id=%s", job_id)
        return _stub_variants(
            title=title,
            salary_text=salary_text,
            location_district=location_district,
            location_city=location_city,
            target_hires=target_hires,
            company_name=company_name,
        )

    client = get_claude()
    system_prompt = load_prompt("job_generator")

    user_text = (
        "<job>\n"
        f"- Công ty: {company_name or '(không rõ)'}\n"
        f"- Chức danh: {title}\n"
        f"- Lương: {salary_text or '(không rõ)'}\n"
        f"- Địa điểm: {location_district}, {location_city}\n"
        f"- Ca: {shift or '(không rõ)'}\n"
        f"- Bắt đầu: {start_date or '(không rõ)'}\n"
        f"- Yêu cầu: {requirements_raw or '(không rõ)'}\n"
        f"- Số tuyển: {target_hires}\n"
        "</job>\n\nTạo 1 bài đăng. Gọi tool emit_variants."
    )

    result = await client.call(
        model=settings.model_job_post,
        system=system_prompt,
        messages=[{"role": "user", "content": user_text}],
        tools=[_TOOL_SCHEMA],
        tool_choice={"type": "tool", "name": "emit_variants"},
        max_tokens=2500,
        call_site="job_post_gen",
        related_id=job_id,
        db=db,
    )

    payload = extract_tool_use(result.content, "emit_variants")
    if not payload or "variants" not in payload:
        raise ClaudeUnavailableError("emit_variants tool not returned")

    return {
        "variants": payload["variants"],
        "warnings": payload.get("warnings", []),
        "token_usage": {
            "input": result.input_tokens,
            "cached": result.cached_tokens,
            "output": result.output_tokens,
            "cost_usd": float(result.cost_usd),
        },
    }
