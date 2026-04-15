from __future__ import annotations

from typing import Any

import sentry_sdk
from starlette.types import ASGIApp, Receive, Scope, Send


def configure_sentry(dsn: str | None) -> None:
    """Initialise Sentry if a DSN is provided; silently skip otherwise."""
    if not dsn:
        return
    sentry_sdk.init(dsn=dsn, traces_sample_rate=1.0)


class SentryBreadcrumbMiddleware:
    """Raw ASGI middleware that adds a Sentry breadcrumb for every HTTP request."""

    def __init__(self, app: ASGIApp, **_kwargs: Any) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] == "http":
            method = scope.get("method", "")
            path = scope.get("path", "")
            sentry_sdk.add_breadcrumb(
                category="http",
                message=f"{method} {path}",
                level="info",
            )
        await self.app(scope, receive, send)
