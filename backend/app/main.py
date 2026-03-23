from __future__ import annotations

import sentry_sdk
from fastapi import FastAPI

from app.api.health import router as health_router
from app.core.config import settings


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    if settings.SENTRY_DSN:
        sentry_sdk.init(dsn=settings.SENTRY_DSN, traces_sample_rate=1.0)

    app = FastAPI(
        title="FlowDay API",
        description="AI-powered daily planner for freelancers",
        version="0.1.0",
    )

    app.include_router(health_router)

    return app


app = create_app()
