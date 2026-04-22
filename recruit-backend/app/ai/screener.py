"""Claude Haiku screener — one turn per call.

Edge case 5: falls back to rule-based parser on failure.
"""
from __future__ import annotations

import logging
import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.client import ClaudeUnavailableError, extract_tool_use, get_claude
from app.ai.fallback_parser import parse_message_fallback
from app.ai.prompts import load as load_prompt
from app.config import get_settings

logger = logging.getLogger(__name__)


_TOOL_SCHEMA: dict[str, Any] = {
    "name": "emit_turn",
    "description": "Emit the AI reply, extracted info so far, and whether screening is done.",
    "input_schema": {
        "type": "object",
        "required": ["reply", "extracted_delta", "done"],
        "properties": {
            "reply": {"type": "string", "maxLength": 160},
            "extracted_delta": {
                "type": "object",
                "properties": {
                    "start_date": {"type": ["string", "null"]},
                    "shift_availability": {
                        "type": "object",
                        "properties": {
                            "day": {"type": "boolean"},
                            "night": {"type": "boolean"},
                            "rotating": {"type": "boolean"},
                            "preferred": {"enum": ["day", "night", "rotating", "any"]},
                        },
                    },
                    "experience": {
                        "type": "object",
                        "properties": {
                            "has_experience": {"type": "boolean"},
                            "years": {"type": ["number", "null"]},
                            "related_keywords": {"type": "array", "items": {"type": "string"}},
                            "willing_to_learn": {"type": "boolean"},
                        },
                    },
                    "questions_from_candidate": {"type": "array", "items": {"type": "string"}},
                    "normalized_location": {
                        "type": "object",
                        "properties": {
                            "district": {"type": "string"},
                            "city": {"type": "string"},
                        },
                    },
                    "hours_per_day": {"type": ["number", "null"], "minimum": 1, "maximum": 24},
                    "prefers_proximity": {"type": "boolean"},
                },
            },
            "done": {"type": "boolean"},
            "next_focus": {"enum": ["start_date", "shift", "experience", "questions", "none"]},
        },
    },
}


async def run_screening_turn(
    *,
    db: AsyncSession,
    session_id: uuid.UUID,
    job_context: dict[str, Any],
    extracted_so_far: dict[str, Any],
    turn_index: int,
    history: list[dict[str, str]],
    user_message: str,
    use_cache: bool = True,
) -> dict[str, Any]:
    """Invoke Claude Haiku for one screening turn.

    If Claude fails twice (handled inside client), returns fallback payload from regex parser.
    Always returns a dict with keys: reply, extracted_delta, done, fallback_used.
    """
    client = get_claude()
    settings = get_settings()
    system_text = load_prompt("screener")

    system: list[dict[str, Any]] = [
        {"type": "text", "text": system_text, "cache_control": {"type": "ephemeral"}} if use_cache
        else {"type": "text", "text": system_text}
    ]

    job_ctx_text = (
        f"{job_context.get('title','?')} | {job_context.get('location_district','?')}, "
        f"{job_context.get('location_city','?')} | ca: {job_context.get('shift','?')} | "
        f"yêu cầu: {job_context.get('requirements_raw','?')}"
    )

    user_content = (
        f"<job_context>\n{job_ctx_text}\n</job_context>\n\n"
        f"<state>\nturn: {turn_index}/5\nextracted: {_json(extracted_so_far)}\n</state>\n\n"
        f"<history>\n{_render_history(history)}\n</history>\n\n"
        f"<user_msg>\n{user_message}\n</user_msg>\n\nGọi emit_turn."
    )

    try:
        result = await client.call(
            model=settings.model_screening,
            system=system,
            messages=[{"role": "user", "content": user_content}],
            tools=[_TOOL_SCHEMA],
            tool_choice={"type": "tool", "name": "emit_turn"},
            max_tokens=600,
            call_site="screening_turn",
            related_id=session_id,
            db=db,
        )
    except ClaudeUnavailableError:
        logger.warning("screener.fallback session_id=%s turn=%d", session_id, turn_index)
        return _fallback_turn(user_message, turn_index, extracted_so_far)

    payload = extract_tool_use(result.content, "emit_turn")
    if not payload or "reply" not in payload:
        logger.warning("screener.invalid_tool session_id=%s", session_id)
        return _fallback_turn(user_message, turn_index, extracted_so_far)

    return {
        "reply": payload.get("reply", "Dạ cảm ơn anh/chị."),
        "extracted_delta": payload.get("extracted_delta", {}),
        "done": bool(payload.get("done", False)),
        "fallback_used": False,
    }


def _fallback_turn(user_msg: str, turn_index: int, extracted_so_far: dict[str, Any]) -> dict[str, Any]:
    """Sequential fallback — one question per turn + turn-aware heuristic extraction.

    Landing asked start_date → Turn 1 answer = start_date.
    Turn 2 answer = shift. Turn 3 answer = experience. Turn 4 answer = questions.

    On each turn, if regex parser missed the expected field, apply a turn-aware
    heuristic so short answers ("mai", "xoay", "chưa", "không") still extract.
    """
    from app.utils.vietnamese import normalize_for_match

    delta = parse_message_fallback(user_msg)
    canon = normalize_for_match(user_msg).strip()

    # idx = turn_index - 1 (1-based turn → 0-based question idx)
    question_sequence = [
        "Dạ cảm ơn anh/chị. Anh/chị làm được ca ngày, ca đêm, hay ca xoay ạ?",
        "Anh/chị đã từng làm công việc tương tự chưa? Hoặc ngành khác cũng được ạ.",
        "Anh/chị có câu hỏi gì muốn hỏi nhà tuyển dụng không ạ? Nếu không thì em gửi hồ sơ luôn.",
        "Dạ em đã nhận đủ thông tin. Cảm ơn anh/chị nhiều 🙏",
    ]
    idx = max(0, min(turn_index - 1, len(question_sequence) - 1))
    reply = question_sequence[idx]

    # ─── Turn-aware heuristic extraction ─────────────────────────────
    # Turn 1: answering start_date ("Anh đi làm được từ khi nào?")
    if turn_index == 1 and not delta.get("start_date"):
        if any(k in canon for k in ("mai", "nay", "hom nay", "ngay mai", "lien", "ngay")):
            delta["start_date"] = "asap"
        elif "tuan sau" in canon:
            delta["start_date"] = "next_week"
        elif "thang sau" in canon:
            delta["start_date"] = "next_month"
        else:
            # Candidate said something we can't parse — record that they answered
            delta["start_date"] = "asap"

    # Turn 2: answering shift. parse_message_fallback handles "ngay"/"dem"/"xoay".
    # If still empty, assume "flexible" since user did respond.
    if turn_index == 2 and not delta.get("shift_availability"):
        delta["shift_availability"] = {
            "day": True, "night": True, "rotating": True, "preferred": "any",
        }

    # Turn 3: answering experience.
    if turn_index == 3 and not delta.get("experience"):
        yes_tokens = ("co", "có", "roi", "rồi", "da", "đã", "yes", "lam roi", "lam lau")
        no_tokens = ("chua", "chưa", "khong", "không", "no", "k", "kh")
        if canon in yes_tokens or any(canon.startswith(t + " ") for t in yes_tokens):
            delta["experience"] = {"has_experience": True, "willing_to_learn": True, "related_keywords": []}
        elif canon in no_tokens or any(canon.startswith(t + " ") for t in no_tokens):
            delta["experience"] = {"has_experience": False, "willing_to_learn": True, "related_keywords": []}
        else:
            # Any other answer → assume no experience, willing to learn (most common for blue-collar)
            delta["experience"] = {"has_experience": False, "willing_to_learn": True, "related_keywords": []}

    # Turn 4: answering "any questions?". Always record as asked.
    if turn_index >= 4 and "questions_from_candidate" not in delta:
        # Short "no" variants → empty list. Otherwise treat the message as a question.
        no_tokens = ("khong", "không", "k", "kh", "no", "khong co", "không có", "khong hoi")
        if canon in no_tokens or any(canon.startswith(t + " ") for t in no_tokens) or len(canon) <= 4:
            delta["questions_from_candidate"] = []
        else:
            delta["questions_from_candidate"] = [user_msg.strip()]

    # Done only after Turn 4 (user answered all 4 questions)
    done = turn_index >= 4 or idx >= len(question_sequence) - 1

    return {
        "reply": reply,
        "extracted_delta": delta,
        "done": done,
        "fallback_used": True,
    }


def _render_history(history: list[dict[str, str]]) -> str:
    return "\n".join(f"[{m['role']}] {m['content']}" for m in history[-8:])


def _json(obj: Any) -> str:
    import json as _json_mod
    return _json_mod.dumps(obj, ensure_ascii=False)
