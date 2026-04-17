from __future__ import annotations

from fastapi import FastAPI
from prometheus_client import CollectorRegistry, Counter, Histogram
from prometheus_fastapi_instrumentator import Instrumentator

# AI Agent metric placeholders — scaffolding for the future agent pipeline
agent_latency_seconds: Histogram = Histogram(
    "agent_latency_seconds",
    "Time spent in an AI agent call",
    labelnames=["agent_name"],
    buckets=(0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
)

token_cost_total: Counter = Counter(
    "token_cost_total",
    "Cumulative token cost across all AI agent calls",
    labelnames=["agent_name", "model"],
)

judge_score: Histogram = Histogram(
    "judge_score",
    "Score assigned by the judge agent",
    labelnames=["agent_name"],
    buckets=(10, 20, 30, 40, 50, 60, 70, 80, 90, 100),
)


def configure_metrics(
    app: FastAPI,
    *,
    enabled: bool = True,
    registry: CollectorRegistry | None = None,
) -> None:
    """Instrument the app with Prometheus metrics; silently skip when disabled.

    Args:
        app: The FastAPI application to instrument.
        enabled: When False, no instrumentation is applied (useful for testing
            or environments that use a different scraping stack).
        registry: Optional CollectorRegistry; defaults to the global REGISTRY.
            Pass a fresh CollectorRegistry() in tests to avoid duplicate-metric
            errors if multiple Instrumentator instances are created in one process.
    """
    if not enabled:
        return
    Instrumentator(registry=registry).instrument(app).expose(app, endpoint="/metrics")
