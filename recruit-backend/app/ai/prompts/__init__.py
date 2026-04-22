"""Prompt template loader."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

_PROMPT_DIR = Path(__file__).parent


@lru_cache(maxsize=16)
def load(name: str) -> str:
    """Load a .txt prompt by name, stripping trailing whitespace."""
    path = _PROMPT_DIR / f"{name}.txt"
    if not path.exists():
        raise FileNotFoundError(f"Prompt template not found: {name}")
    return path.read_text(encoding="utf-8").rstrip()
