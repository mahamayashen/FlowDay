"""Integration tests for /weekly-reviews — real DB, patched agent pipeline."""

from __future__ import annotations

import uuid
from collections.abc import Iterator
from datetime import date
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient

from app.agents.schemas import (
    GroupAResult,
    JudgeResult,
    NarrativeWriterResult,
    PatternDetectorResult,
)


@pytest.fixture
def patched_pipeline() -> Iterator[None]:
    """Patch the four orchestrator entry points with deterministic stub outputs.

    Integration tests exercise the API + DB layer but must not hit real LLMs.
    """
    group_a = GroupAResult()
    pattern = PatternDetectorResult(patterns=[], summary="integration-stub")
    narrative = NarrativeWriterResult(
        executive_summary="Executive summary.",
        time_analysis="Time analysis.",
        productivity_patterns="Patterns.",
        areas_of_concern="Concerns.",
    )
    judge = JudgeResult(
        actionability_score=8,
        accuracy_score=9,
        coherence_score=7,
        overall_score=8,
        feedback="integration-stub",
    )
    with (
        patch(
            "app.services.weekly_review_service.run_group_a",
            new=AsyncMock(return_value=group_a),
        ),
        patch(
            "app.services.weekly_review_service.run_group_b",
            new=AsyncMock(return_value=pattern),
        ),
        patch(
            "app.services.weekly_review_service.run_group_c",
            new=AsyncMock(return_value=narrative),
        ),
        patch(
            "app.services.weekly_review_service.run_group_d",
            new=AsyncMock(return_value=judge),
        ),
    ):
        yield


# ── POST /weekly-reviews/generate ─────────────────────────────────────────────


async def test_post_generate_persists_review_to_db(
    auth_client: AsyncClient, patched_pipeline: None
) -> None:
    resp = await auth_client.post(
        "/weekly-reviews/generate", params={"week_start": "2026-04-13"}
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "complete"
    assert body["week_start"] == "2026-04-13"
    assert body["narrative"].startswith("Executive summary.")
    assert body["scores_json"]["overall_score"] == 8
    assert body["agent_metadata_json"]["stages"]["group_a"]["latency_ms"] >= 0


async def test_post_generate_normalizes_wednesday_to_monday(
    auth_client: AsyncClient, patched_pipeline: None
) -> None:
    resp = await auth_client.post(
        "/weekly-reviews/generate", params={"week_start": "2026-04-15"}
    )
    assert resp.status_code == 200
    # 2026-04-15 is a Wednesday — stored row must be keyed by Monday 2026-04-13.
    assert resp.json()["week_start"] == "2026-04-13"


async def test_post_generate_is_idempotent_for_same_week(
    auth_client: AsyncClient, patched_pipeline: None
) -> None:
    """Re-generating within the same week reuses the row, not a new one."""
    first = await auth_client.post(
        "/weekly-reviews/generate", params={"week_start": "2026-04-13"}
    )
    second = await auth_client.post(
        "/weekly-reviews/generate", params={"week_start": "2026-04-15"}
    )
    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["id"] == second.json()["id"]

    listing = await auth_client.get("/weekly-reviews")
    assert listing.status_code == 200
    assert len(listing.json()) == 1


async def test_post_generate_requires_auth(client: AsyncClient) -> None:
    resp = await client.post(
        "/weekly-reviews/generate", params={"week_start": "2026-04-13"}
    )
    assert resp.status_code == 401


# ── GET /weekly-reviews (list) ────────────────────────────────────────────────


async def test_list_weekly_reviews_empty_returns_empty_array(
    auth_client: AsyncClient,
) -> None:
    resp = await auth_client.get("/weekly-reviews")
    assert resp.status_code == 200
    assert resp.json() == []


async def test_list_weekly_reviews_scopes_to_current_user(
    auth_client: AsyncClient,
    other_auth_client: AsyncClient,
    patched_pipeline: None,
) -> None:
    await auth_client.post(
        "/weekly-reviews/generate", params={"week_start": "2026-04-13"}
    )
    await other_auth_client.post(
        "/weekly-reviews/generate", params={"week_start": "2026-04-13"}
    )

    resp_a = await auth_client.get("/weekly-reviews")
    resp_b = await other_auth_client.get("/weekly-reviews")
    assert resp_a.status_code == 200
    assert resp_b.status_code == 200
    assert len(resp_a.json()) == 1
    assert len(resp_b.json()) == 1
    assert resp_a.json()[0]["id"] != resp_b.json()[0]["id"]


async def test_list_weekly_reviews_orders_by_week_start_desc(
    auth_client: AsyncClient, patched_pipeline: None
) -> None:
    for week in ("2026-03-30", "2026-04-13", "2026-04-06"):
        await auth_client.post("/weekly-reviews/generate", params={"week_start": week})

    resp = await auth_client.get("/weekly-reviews")
    weeks = [r["week_start"] for r in resp.json()]
    assert weeks == ["2026-04-13", "2026-04-06", "2026-03-30"]


# ── GET /weekly-reviews/{review_id} ───────────────────────────────────────────


async def test_get_weekly_review_by_id_returns_stored_review(
    auth_client: AsyncClient, patched_pipeline: None
) -> None:
    created = await auth_client.post(
        "/weekly-reviews/generate", params={"week_start": "2026-04-13"}
    )
    review_id = created.json()["id"]

    resp = await auth_client.get(f"/weekly-reviews/{review_id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == review_id
    assert resp.json()["scores_json"]["overall_score"] == 8


async def test_get_other_users_weekly_review_returns_404(
    auth_client: AsyncClient,
    other_auth_client: AsyncClient,
    patched_pipeline: None,
) -> None:
    """Reading another user's review must 404, never leak the record."""
    created = await other_auth_client.post(
        "/weekly-reviews/generate", params={"week_start": "2026-04-13"}
    )
    foreign_id = created.json()["id"]

    resp = await auth_client.get(f"/weekly-reviews/{foreign_id}")
    assert resp.status_code == 404


async def test_get_nonexistent_weekly_review_returns_404(
    auth_client: AsyncClient,
) -> None:
    resp = await auth_client.get(f"/weekly-reviews/{uuid.uuid4()}")
    assert resp.status_code == 404


async def test_get_weekly_review_by_id_requires_auth(client: AsyncClient) -> None:
    resp = await client.get(f"/weekly-reviews/{uuid.uuid4()}")
    assert resp.status_code == 401


# ── Failure path ──────────────────────────────────────────────────────────────


async def test_post_generate_marks_review_failed_when_pipeline_raises(
    auth_client: AsyncClient,
) -> None:
    """If Group A fails, the review row is persisted with status=failed."""
    with (
        patch(
            "app.services.weekly_review_service.run_group_a",
            new=AsyncMock(side_effect=RuntimeError("upstream down")),
        ),
        pytest.raises(RuntimeError, match="upstream down"),
    ):
        await auth_client.post(
            "/weekly-reviews/generate", params={"week_start": "2026-04-13"}
        )

    # Row must still exist with status=failed so the frontend can surface the error.
    week_start_iso = date(2026, 4, 13).isoformat()
    listing = await auth_client.get("/weekly-reviews")
    assert listing.status_code == 200
    matches = [r for r in listing.json() if r["week_start"] == week_start_iso]
    assert len(matches) == 1
    assert matches[0]["status"] == "failed"
    assert "group_a" in matches[0]["agent_metadata_json"]["stages"]
