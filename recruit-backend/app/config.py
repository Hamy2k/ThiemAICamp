"""Application configuration loaded from environment variables."""
from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """All runtime config. Every env var referenced by the app is declared here."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Database
    database_url: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/recruit",
        description="Async Postgres URL. Must use asyncpg driver.",
    )

    # Claude API
    anthropic_api_key: str = Field(default="", description="Claude API key")
    ai_gateway_base_url: str | None = Field(
        default=None,
        description="Optional Vercel AI Gateway base URL",
    )

    # Models
    model_job_post: str = "claude-sonnet-4-6"
    model_screening: str = "claude-haiku-4-5-20251001"
    model_scoring: str = "claude-haiku-4-5-20251001"

    # Telegram
    telegram_bot_token: str = ""
    telegram_webhook_secret: str = ""

    # App
    app_env: str = "development"
    log_level: str = "INFO"
    cors_origins: str = "http://localhost:3000,http://localhost:5173"

    # Idempotency / rate limits
    idempotency_window_seconds: int = 600
    rate_limit_ip_per_10min: int = 5
    rate_limit_phone_per_hour: int = 3

    # Claude call policy
    claude_timeout_seconds: float = 10.0
    claude_retry_count: int = 1
    claude_retry_backoff_ms: int = 500

    # Telegram call policy
    telegram_timeout_seconds: float = 5.0

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
