from __future__ import annotations

import uuid

from httpx import AsyncClient

# ── Helpers ───────────────────────────────────────────────────────────────────

_DATE = "2024-06-17"


async def _create_task(client: AsyncClient) -> str:
    """Create a project and task, return task_id."""
    resp = await client.post(
        "/projects", json={"name": "Test Project", "color": "#000000"}
    )
    assert resp.status_code == 201
    project_id = resp.json()["id"]
    resp = await client.post(
        f"/projects/{project_id}/tasks", json={"title": "Test Task"}
    )
    assert resp.status_code == 201
    return resp.json()["id"]


# ── Create ────────────────────────────────────────────────────────────────────


async def test_create_schedule_block_returns_201(auth_client: AsyncClient) -> None:
    task_id = await _create_task(auth_client)
    resp = await auth_client.post(
        "/schedule-blocks",
        json={"task_id": task_id, "date": _DATE, "start_hour": 9.0, "end_hour": 11.0},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["task_id"] == task_id
    assert float(body["start_hour"]) == 9.0
    assert float(body["end_hour"]) == 11.0
    assert body["source"] == "manual"
    assert "id" in body


# ── List ──────────────────────────────────────────────────────────────────────


async def test_list_schedule_blocks_for_date(auth_client: AsyncClient) -> None:
    task_id = await _create_task(auth_client)
    await auth_client.post(
        "/schedule-blocks",
        json={"task_id": task_id, "date": _DATE, "start_hour": 9.0, "end_hour": 10.0},
    )
    await auth_client.post(
        "/schedule-blocks",
        json={"task_id": task_id, "date": _DATE, "start_hour": 11.0, "end_hour": 12.0},
    )
    resp = await auth_client.get(f"/schedule-blocks?date={_DATE}")
    assert resp.status_code == 200
    assert len(resp.json()) >= 2


# ── Get ───────────────────────────────────────────────────────────────────────


async def test_get_schedule_block_by_id(auth_client: AsyncClient) -> None:
    task_id = await _create_task(auth_client)
    create_resp = await auth_client.post(
        "/schedule-blocks",
        json={"task_id": task_id, "date": _DATE, "start_hour": 14.0, "end_hour": 15.0},
    )
    block_id = create_resp.json()["id"]

    resp = await auth_client.get(f"/schedule-blocks/{block_id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == block_id
    assert float(resp.json()["start_hour"]) == 14.0


async def test_get_nonexistent_block_returns_404(auth_client: AsyncClient) -> None:
    resp = await auth_client.get(f"/schedule-blocks/{uuid.uuid4()}")
    assert resp.status_code == 404


# ── Update ────────────────────────────────────────────────────────────────────


async def test_update_schedule_block_time(auth_client: AsyncClient) -> None:
    task_id = await _create_task(auth_client)
    create_resp = await auth_client.post(
        "/schedule-blocks",
        json={"task_id": task_id, "date": _DATE, "start_hour": 9.0, "end_hour": 10.0},
    )
    block_id = create_resp.json()["id"]

    resp = await auth_client.put(
        f"/schedule-blocks/{block_id}",
        json={"start_hour": 10.0, "end_hour": 12.0},
    )
    assert resp.status_code == 200
    assert float(resp.json()["start_hour"]) == 10.0
    assert float(resp.json()["end_hour"]) == 12.0


# ── Delete ────────────────────────────────────────────────────────────────────


async def test_delete_schedule_block_returns_204(auth_client: AsyncClient) -> None:
    task_id = await _create_task(auth_client)
    create_resp = await auth_client.post(
        "/schedule-blocks",
        json={"task_id": task_id, "date": _DATE, "start_hour": 16.0, "end_hour": 17.0},
    )
    block_id = create_resp.json()["id"]

    resp = await auth_client.delete(f"/schedule-blocks/{block_id}")
    assert resp.status_code == 204

    get_resp = await auth_client.get(f"/schedule-blocks/{block_id}")
    assert get_resp.status_code == 404


# ── Ownership scoping ────────────────────────────────────────────────────────


async def test_other_user_block_returns_404(
    auth_client: AsyncClient, other_auth_client: AsyncClient
) -> None:
    """User B cannot access User A's schedule block."""
    task_id = await _create_task(auth_client)
    create_resp = await auth_client.post(
        "/schedule-blocks",
        json={"task_id": task_id, "date": _DATE, "start_hour": 8.0, "end_hour": 9.0},
    )
    block_id = create_resp.json()["id"]

    resp = await other_auth_client.get(f"/schedule-blocks/{block_id}")
    assert resp.status_code == 404
