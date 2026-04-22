from __future__ import annotations

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # Server
    PORT: int = 5060

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://flowday:flowday@localhost:5432/flowday"

    # Cache
    REDIS_URL: str = "redis://localhost:6379/0"

    # Security
    SECRET_KEY: str = "change-me-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # OAuth — Google
    GOOGLE_CLIENT_ID: str | None = None
    GOOGLE_CLIENT_SECRET: str | None = None
    # Note: port 5060 is blocked by Chromium;
    # override via .env in browser-testing scenarios
    GOOGLE_REDIRECT_URI: str = "http://localhost:5060/auth/google/callback"

    # OAuth — Google Calendar (separate scope from login OAuth)
    GOOGLE_CALENDAR_REDIRECT_URI: str = (
        "http://localhost:5060/sync/google-calendar/callback"
    )

    # OAuth — GitHub
    GITHUB_CLIENT_ID: str | None = None
    GITHUB_CLIENT_SECRET: str | None = None
    GITHUB_REDIRECT_URI: str = "http://localhost:5060/auth/github/callback"
    GITHUB_SYNC_REDIRECT_URI: str = "http://localhost:5060/sync/github/callback"

    # AI / LLM (provider-agnostic pydantic-ai model strings)
    # Narrative Writer and Judge MUST use different providers (CLAUDE.md).
    # Google retired gemini-1.5-flash and started blocking new users on
    # gemini-2.0-flash; use 2.5-pro for Judge. Narrative Writer is on the
    # project's standardized OpenAI nano snapshot.
    LLM_MODEL: str = "openai:gpt-5.4-nano-2026-03-17"
    LLM_JUDGE_MODEL: str = "google-gla:gemini-2.5-pro"

    # Judge agent — minimum acceptable score per dimension (1–10); triggers retry below
    JUDGE_SCORE_THRESHOLD: int = 6

    # CORS — comma-separated list of origins allowed to call the API from
    # the browser. Empty by default so production is locked down unless
    # explicitly configured. In dev it's unnecessary because Vite proxies
    # all API calls through the same origin.
    BACKEND_CORS_ORIGINS: str = ""

    # Monitoring (optional — silently disabled when absent)
    SENTRY_DSN: str | None = None
    PROMETHEUS_ENABLED: bool = True

    # Feature flags
    PII_ANONYMIZATION_ENABLED: bool = True

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def _coerce_asyncpg_scheme(cls, v: str) -> str:
        """Rewrite `postgresql://` → `postgresql+asyncpg://`.

        Managed Postgres providers (Railway, Heroku, Supabase, …) inject a
        connection string with the bare `postgresql://` scheme, but our
        SQLAlchemy engine is async and requires the `asyncpg` driver. Doing
        this at config-load time means the rest of the codebase can stay
        driver-agnostic and there's no env-var-rewriting step to remember
        on every deploy.
        """
        if v.startswith("postgresql://"):
            return "postgresql+asyncpg://" + v[len("postgresql://") :]
        if v.startswith("postgres://"):
            # Heroku-style shorthand, same fix
            return "postgresql+asyncpg://" + v[len("postgres://") :]
        return v

    @property
    def backend_cors_origins(self) -> list[str]:
        """Parse BACKEND_CORS_ORIGINS into a whitespace-trimmed list,
        dropping empty items."""
        return [
            origin.strip()
            for origin in self.BACKEND_CORS_ORIGINS.split(",")
            if origin.strip()
        ]


settings = Settings()
