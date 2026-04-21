"""Unit tests for `app.core.config.Settings` — especially the list-valued
fields that are parsed from comma-separated env vars."""

from __future__ import annotations

from app.core.config import Settings


class TestBackendCorsOrigins:
    def test_empty_string_yields_empty_list(self) -> None:
        """Unset / blank env var disables CORS (no allowed origins)."""
        s = Settings(BACKEND_CORS_ORIGINS="")
        assert s.backend_cors_origins == []

    def test_single_origin(self) -> None:
        s = Settings(BACKEND_CORS_ORIGINS="https://flow-day.vercel.app")
        assert s.backend_cors_origins == ["https://flow-day.vercel.app"]

    def test_multiple_origins_comma_separated(self) -> None:
        s = Settings(
            BACKEND_CORS_ORIGINS=(
                "https://flow-day.vercel.app,https://staging.flow-day.app"
            )
        )
        assert s.backend_cors_origins == [
            "https://flow-day.vercel.app",
            "https://staging.flow-day.app",
        ]

    def test_whitespace_around_origins_is_trimmed(self) -> None:
        s = Settings(
            BACKEND_CORS_ORIGINS=("  https://a.com  ,  https://b.com  ,https://c.com")
        )
        assert s.backend_cors_origins == [
            "https://a.com",
            "https://b.com",
            "https://c.com",
        ]

    def test_empty_items_are_dropped(self) -> None:
        """Trailing commas / double commas should not produce empty-string origins."""
        s = Settings(BACKEND_CORS_ORIGINS="https://a.com,,https://b.com,")
        assert s.backend_cors_origins == ["https://a.com", "https://b.com"]


def test_default_backend_cors_origins_is_empty() -> None:
    """With no env var set, production is locked down by default."""
    s = Settings()
    assert s.backend_cors_origins == []


class TestDatabaseUrlAsyncpgCoercion:
    """Managed Postgres providers give us `postgresql://` URLs. Our async
    SQLAlchemy engine requires `postgresql+asyncpg://`. The validator must
    rewrite automatically so deploy env vars don't need manual assembly.
    """

    def test_postgresql_scheme_is_rewritten(self) -> None:
        s = Settings(DATABASE_URL="postgresql://u:p@host:5432/db")
        assert s.DATABASE_URL == "postgresql+asyncpg://u:p@host:5432/db"

    def test_postgres_shorthand_is_rewritten(self) -> None:
        """Heroku-style `postgres://` shorthand also needs coercion."""
        s = Settings(DATABASE_URL="postgres://u:p@host:5432/db")
        assert s.DATABASE_URL == "postgresql+asyncpg://u:p@host:5432/db"

    def test_already_asyncpg_scheme_is_left_alone(self) -> None:
        url = "postgresql+asyncpg://u:p@host:5432/db"
        s = Settings(DATABASE_URL=url)
        assert s.DATABASE_URL == url

    def test_query_params_preserved(self) -> None:
        s = Settings(DATABASE_URL="postgresql://u:p@host:5432/db?sslmode=require")
        assert s.DATABASE_URL == (
            "postgresql+asyncpg://u:p@host:5432/db?sslmode=require"
        )
