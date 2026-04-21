"""Integration tests for the CORS middleware.

CORS is applied only when `BACKEND_CORS_ORIGINS` is non-empty, so we build
a fresh app with overridden settings for each scenario rather than reusing
the module-level `app` singleton.
"""

from __future__ import annotations

import importlib
from collections.abc import Callable, Generator

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient


@pytest.fixture
def rebuild_app_with_cors(
    monkeypatch: pytest.MonkeyPatch,
) -> Generator[Callable[[str], FastAPI], None, None]:
    """Return a factory that rebuilds the app with a specific CORS allowlist."""

    def _factory(origins: str) -> FastAPI:
        # Reload config module so `settings = Settings()` re-reads env.
        monkeypatch.setenv("BACKEND_CORS_ORIGINS", origins)
        import app.core.config as config_module

        importlib.reload(config_module)
        import app.main as main_module

        importlib.reload(main_module)
        return main_module.create_app()

    yield _factory

    # Restore a clean settings module so other tests see the default.
    import app.core.config as config_module

    importlib.reload(config_module)
    import app.main as main_module

    importlib.reload(main_module)


@pytest.mark.asyncio
async def test_preflight_from_allowed_origin_gets_cors_headers(
    rebuild_app_with_cors: Callable[[str], FastAPI],
) -> None:
    app = rebuild_app_with_cors("https://flow-day.vercel.app")

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        resp = await client.options(
            "/health",
            headers={
                "Origin": "https://flow-day.vercel.app",
                "Access-Control-Request-Method": "GET",
            },
        )

    # Starlette's CORSMiddleware returns 200 for preflight on allowed origins
    assert resp.status_code == 200
    assert (
        resp.headers.get("access-control-allow-origin") == "https://flow-day.vercel.app"
    )
    assert resp.headers.get("access-control-allow-credentials") == "true"


@pytest.mark.asyncio
async def test_preflight_from_disallowed_origin_gets_no_cors_headers(
    rebuild_app_with_cors: Callable[[str], FastAPI],
) -> None:
    app = rebuild_app_with_cors("https://flow-day.vercel.app")

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        resp = await client.options(
            "/health",
            headers={
                "Origin": "https://evil.example.com",
                "Access-Control-Request-Method": "GET",
            },
        )

    # Starlette refuses to echo the origin back, which is what browsers
    # use to enforce the block.
    assert resp.headers.get("access-control-allow-origin") != (
        "https://evil.example.com"
    )


@pytest.mark.asyncio
async def test_no_cors_middleware_when_origins_empty(
    rebuild_app_with_cors: Callable[[str], FastAPI],
) -> None:
    """Default prod posture: empty allowlist → no CORS middleware at all."""
    app = rebuild_app_with_cors("")

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        resp = await client.options(
            "/health",
            headers={
                "Origin": "https://flow-day.vercel.app",
                "Access-Control-Request-Method": "GET",
            },
        )

    # Without CORSMiddleware the OPTIONS handler either 405s or passes
    # through without adding CORS headers — the key assertion is that no
    # Access-Control-Allow-Origin header is set.
    assert "access-control-allow-origin" not in {k.lower() for k in resp.headers}
