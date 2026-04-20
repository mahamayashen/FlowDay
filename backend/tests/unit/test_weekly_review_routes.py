from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.database import get_db
from app.core.deps import get_current_user
from app.main import app
from app.models.weekly_review import ReviewStatus, WeeklyReview

USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")
REVIEW_ID = uuid.UUID("00000000-0000-0000-0000-000000000002")


def _make_fake_user() -> MagicMock:
    fake = MagicMock()
    fake.id = USER_ID
    fake.email = "test@example.com"
    fake.name = "Test User"
    return fake


def _make_review(status: str = ReviewStatus.COMPLETE) -> WeeklyReview:
    review = WeeklyReview(
        user_id=USER_ID,
        week_start=date(2026, 4, 13),
        raw_data_json={},
        status=status,
    )
    review.id = REVIEW_ID
    review.narrative = "Executive summary.\n\nTime analysis.\n\nPatterns.\n\nConcerns."
    review.scores_json = {
        "actionability_score": 8,
        "accuracy_score": 9,
        "coherence_score": 7,
        "overall_score": 8,
        "feedback": "good",
    }
    review.insights_json = {}
    review.agent_metadata_json = {"analysis_date": "2026-04-13", "judge_scored": True}
    return review


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac


def _setup_overrides() -> None:
    app.dependency_overrides[get_current_user] = _make_fake_user

    async def override_db() -> AsyncMock:  # type: ignore[misc]
        yield AsyncMock()

    app.dependency_overrides[get_db] = override_db


def _clear_overrides() -> None:
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# POST /weekly-reviews
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_post_weekly_review_triggers_generation_and_returns_response(
    client: AsyncClient,
) -> None:
    """POST /weekly-reviews returns 200 with review fields populated."""
    _setup_overrides()
    review = _make_review()
    try:
        with (
            patch(
                "app.api.weekly_reviews.get_or_create_review",
                new_callable=AsyncMock,
                return_value=review,
            ),
            patch(
                "app.api.weekly_reviews.generate_review",
                new_callable=AsyncMock,
                return_value=review,
            ),
        ):
            resp = await client.post(
                "/weekly-reviews", params={"week_start": "2026-04-13"}
            )
    finally:
        _clear_overrides()

    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == ReviewStatus.COMPLETE
    assert data["week_start"] == "2026-04-13"
    assert "narrative" in data


@pytest.mark.asyncio
async def test_post_weekly_review_requires_auth(client: AsyncClient) -> None:
    """POST /weekly-reviews without auth returns 401."""

    async def override_db() -> AsyncMock:  # type: ignore[misc]
        yield AsyncMock()

    app.dependency_overrides[get_db] = override_db
    try:
        resp = await client.post("/weekly-reviews", params={"week_start": "2026-04-13"})
    finally:
        app.dependency_overrides.clear()
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_post_weekly_review_accepts_week_start_query_param(
    client: AsyncClient,
) -> None:
    """POST /weekly-reviews passes the correct week_start date to the service."""
    _setup_overrides()
    review = _make_review()
    captured: list[date] = []

    async def fake_get_or_create(db, user_id, week_start):  # type: ignore[no-untyped-def]
        captured.append(week_start)
        return review

    try:
        with (
            patch(
                "app.api.weekly_reviews.get_or_create_review",
                side_effect=fake_get_or_create,
            ),
            patch(
                "app.api.weekly_reviews.generate_review",
                new_callable=AsyncMock,
                return_value=review,
            ),
        ):
            await client.post(
                "/weekly-reviews", params={"week_start": "2026-04-15"}
            )
    finally:
        _clear_overrides()

    # week_start 2026-04-15 (Wednesday) → service receives Wednesday; service normalizes to Monday
    assert captured[0] == date(2026, 4, 15)


# ---------------------------------------------------------------------------
# GET /weekly-reviews/{week_start}
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_weekly_review_returns_stored_review(client: AsyncClient) -> None:
    """GET /weekly-reviews/{week_start} returns 200 with the stored review."""
    _setup_overrides()
    review = _make_review()
    try:
        with patch(
            "app.api.weekly_reviews.get_review",
            new_callable=AsyncMock,
            return_value=review,
        ):
            resp = await client.get("/weekly-reviews/2026-04-13")
    finally:
        _clear_overrides()

    assert resp.status_code == 200
    assert resp.json()["week_start"] == "2026-04-13"


@pytest.mark.asyncio
async def test_get_weekly_review_returns_404_when_not_found(
    client: AsyncClient,
) -> None:
    """GET /weekly-reviews/{week_start} returns 404 when no review exists."""
    _setup_overrides()
    try:
        with patch(
            "app.api.weekly_reviews.get_review",
            new_callable=AsyncMock,
            return_value=None,
        ):
            resp = await client.get("/weekly-reviews/2026-04-13")
    finally:
        _clear_overrides()

    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_get_weekly_review_requires_auth(client: AsyncClient) -> None:
    """GET /weekly-reviews/{week_start} without auth returns 401."""

    async def override_db() -> AsyncMock:  # type: ignore[misc]
        yield AsyncMock()

    app.dependency_overrides[get_db] = override_db
    try:
        resp = await client.get("/weekly-reviews/2026-04-13")
    finally:
        app.dependency_overrides.clear()
    assert resp.status_code == 401
