from __future__ import annotations

from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator


def configure_metrics(app: FastAPI, *, enabled: bool = True) -> None:
    """Instrument the app with Prometheus metrics; silently skip when disabled."""
    if not enabled:
        return
    Instrumentator().instrument(app).expose(app, endpoint="/metrics")
