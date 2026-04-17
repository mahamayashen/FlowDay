from __future__ import annotations

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

    # OAuth — GitHub
    GITHUB_CLIENT_ID: str | None = None
    GITHUB_CLIENT_SECRET: str | None = None
    GITHUB_REDIRECT_URI: str = "http://localhost:5060/auth/github/callback"

    # Monitoring (optional — silently disabled when absent)
    SENTRY_DSN: str | None = None
    PROMETHEUS_ENABLED: bool = True


settings = Settings()
