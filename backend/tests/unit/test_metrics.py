from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from prometheus_client import Counter, Histogram

from app.core.metrics import agent_latency_seconds, configure_metrics, judge_score, token_cost_total


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


# ---------------------------------------------------------------------------
# Cycle 2: AI metric placeholder tests
# ---------------------------------------------------------------------------


def test_ai_metrics_registered_as_correct_types() -> None:
    """The AI metric singletons must be the correct prometheus_client types."""
    assert isinstance(agent_latency_seconds, Histogram)
    assert isinstance(token_cost_total, Counter)
    assert isinstance(judge_score, Histogram)


def test_agent_latency_has_agent_name_label() -> None:
    """agent_latency_seconds must carry the 'agent_name' label."""
    assert "agent_name" in agent_latency_seconds._labelnames  # type: ignore[attr-defined]


def test_token_cost_has_agent_name_and_model_labels() -> None:
    """token_cost_total must carry 'agent_name' and 'model' labels."""
    assert "agent_name" in token_cost_total._labelnames  # type: ignore[attr-defined]
    assert "model" in token_cost_total._labelnames  # type: ignore[attr-defined]


async def test_ai_metrics_appear_in_metrics_output() -> None:
    """After observing values, metric names must appear in GET /metrics output."""
    app = FastAPI()
    configure_metrics(app, enabled=True)

    agent_latency_seconds.labels(agent_name="test_agent").observe(0.5)
    token_cost_total.labels(agent_name="test_agent", model="gpt-4").inc(10)
    judge_score.labels(agent_name="test_agent").observe(85)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/metrics")

    body = response.text
    assert "agent_latency_seconds" in body
    assert "token_cost_total" in body
    assert "judge_score" in body
