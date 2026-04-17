from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.core.metrics import configure_metrics


def test_configure_metrics_enabled_instruments_app() -> None:
    """When enabled, Instrumentator must be instantiated, instrumented, and exposed."""
    app = FastAPI()
    with patch("app.core.metrics.Instrumentator") as mock_cls:
        mock_instance = MagicMock()
        mock_cls.return_value = mock_instance
        mock_instance.instrument.return_value = mock_instance

        configure_metrics(app, enabled=True)

        mock_cls.assert_called_once()
        mock_instance.instrument.assert_called_once_with(app)
        mock_instance.expose.assert_called_once()


def test_configure_metrics_disabled_skips_instrumentation() -> None:
    """When disabled, Instrumentator must NOT be instantiated."""
    app = FastAPI()
    with patch("app.core.metrics.Instrumentator") as mock_cls:
        configure_metrics(app, enabled=False)
        mock_cls.assert_not_called()


async def test_metrics_endpoint_returns_200() -> None:
    """A real app with metrics enabled must expose GET /metrics returning 200."""
    app = FastAPI()
    configure_metrics(app, enabled=True)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/metrics")

    assert response.status_code == 200
    assert "text/plain" in response.headers["content-type"]


async def test_metrics_endpoint_absent_when_disabled() -> None:
    """A real app with metrics disabled must NOT have GET /metrics (returns 404)."""
    app = FastAPI()
    configure_metrics(app, enabled=False)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/metrics")

    assert response.status_code == 404
