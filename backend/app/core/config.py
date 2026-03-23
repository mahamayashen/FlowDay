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

    # Monitoring (optional — silently disabled when absent)
    SENTRY_DSN: str | None = None


settings = Settings()
