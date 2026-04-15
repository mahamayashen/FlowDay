from __future__ import annotations

from pydantic import BaseModel


class HealthResponse(BaseModel):
    """Response schema for the health check endpoint."""

    status: str
    database: str
    redis: str


class DependencyDetail(BaseModel):
    """Health detail for a single dependency."""

    status: str
    latency_ms: float


class DetailedHealthResponse(BaseModel):
    """Response schema for the detailed health check endpoint."""

    status: str
    database: DependencyDetail
    redis: DependencyDetail
    sentry_enabled: bool
    version: str
