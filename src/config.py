"""
Centralized configuration for ThiemAICamp.
All hardcoded values live here. Override via environment variables.
"""

import os


def _env(key: str, default: str) -> str:
    return os.environ.get(key, default)


def _env_int(key: str, default: int) -> int:
    return int(os.environ.get(key, str(default)))


def _env_float(key: str, default: float) -> float:
    return float(os.environ.get(key, str(default)))


def _env_bool(key: str, default: bool) -> bool:
    val = os.environ.get(key, str(default)).lower()
    return val in ("true", "1", "yes")


# ── LLM ────────────────────────────────────────────────────────
LLM_MODEL = _env("THIEMAICAMP_MODEL", "claude-sonnet-4-5-20250514")
LLM_TEMPERATURE = _env_float("THIEMAICAMP_TEMPERATURE", 0.0)

# ── Paths ──────────────────────────────────────────────────────
DB_PATH = _env("THIEMAICAMP_DB_PATH", "./data/thiemaicamp.db")
CHROMADB_PATH = _env("THIEMAICAMP_CHROMADB_PATH", "./data/chromadb")
NOTIFICATION_LOG = _env("THIEMAICAMP_NOTIFICATION_LOG", "./data/notifications.log")

# ── Execution ──────────────────────────────────────────────────
SANDBOX_TIMEOUT = _env_int("THIEMAICAMP_SANDBOX_TIMEOUT", 30)
SANDBOX_MAX_OUTPUT = _env_int("THIEMAICAMP_SANDBOX_MAX_OUTPUT", 50000)
TEST_TIMEOUT = _env_int("THIEMAICAMP_TEST_TIMEOUT", 120)

# ── Approval ───────────────────────────────────────────────────
APPROVAL_TIMEOUT = _env_int("THIEMAICAMP_APPROVAL_TIMEOUT", 3600)
APPROVAL_POLL_INTERVAL = _env_float("THIEMAICAMP_APPROVAL_POLL_INTERVAL", 2.0)
DEFAULT_REVIEWER = _env("THIEMAICAMP_DEFAULT_REVIEWER", "Thiem")

# ── Review ─────────────────────────────────────────────────────
REVIEW_MIN_SCORE = _env_float("THIEMAICAMP_REVIEW_MIN_SCORE", 7.0)

# ── Memory ─────────────────────────────────────────────────────
MEMORY_DEDUP_THRESHOLD = _env_float("THIEMAICAMP_MEMORY_DEDUP_THRESHOLD", 0.05)
MEMORY_RELEVANCE_THRESHOLD = _env_float("THIEMAICAMP_MEMORY_RELEVANCE_THRESHOLD", 0.5)

# ── Monitoring ─────────────────────────────────────────────────
LANGSMITH_PROJECT = _env("LANGSMITH_PROJECT", "ThiemAICamp")
METRICS_MAX_MEMORY = _env_int("THIEMAICAMP_METRICS_MAX_MEMORY", 1000)

# ── Webhook ────────────────────────────────────────────────────
WEBHOOK_URL = _env("THIEMAICAMP_WEBHOOK_URL", "")
WEBHOOK_TIMEOUT = _env_int("THIEMAICAMP_WEBHOOK_TIMEOUT", 10)
