from __future__ import annotations

from unittest.mock import patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.sentry import SentryBreadcrumbMiddleware, configure_sentry


def test_configure_sentry_with_dsn_calls_init() -> None:
    """When a DSN is provided, sentry_sdk.init must be called."""
    with patch("app.core.sentry.sentry_sdk") as mock_sdk:
        configure_sentry("https://examplePublicKey@o0.ingest.sentry.io/0")
        mock_sdk.init.assert_called_once()
        call_kwargs = mock_sdk.init.call_args
        assert call_kwargs[1]["dsn"] == "https://examplePublicKey@o0.ingest.sentry.io/0"
        assert call_kwargs[1]["traces_sample_rate"] == 1.0


def test_configure_sentry_without_dsn_skips_init() -> None:
    """When DSN is None, sentry_sdk.init must NOT be called."""
    with patch("app.core.sentry.sentry_sdk") as mock_sdk:
        configure_sentry(None)
        mock_sdk.init.assert_not_called()


def test_configure_sentry_with_empty_dsn_skips_init() -> None:
    """When DSN is empty string, sentry_sdk.init must NOT be called."""
    with patch("app.core.sentry.sentry_sdk") as mock_sdk:
        configure_sentry("")
        mock_sdk.init.assert_not_called()


@pytest.mark.anyio
async def test_breadcrumb_middleware_adds_crumb() -> None:
    """Middleware must add a breadcrumb with method and path for each request."""
    from fastapi import FastAPI

    test_app = FastAPI()

    @test_app.get("/ping")
    async def ping() -> dict[str, str]:
        return {"pong": "ok"}

    test_app.add_middleware(SentryBreadcrumbMiddleware)

    with patch("app.core.sentry.sentry_sdk") as mock_sdk:
        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as client:
            response = await client.get("/ping")

        assert response.status_code == 200
        mock_sdk.add_breadcrumb.assert_called()
        crumb = mock_sdk.add_breadcrumb.call_args[1]
        assert crumb["category"] == "http"
        assert crumb["message"] == "GET /ping"
        assert crumb["level"] == "info"
