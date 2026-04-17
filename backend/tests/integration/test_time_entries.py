from __future__ import annotations

import uuid

from httpx import AsyncClient

# ── Helpers ───────────────────────────────────────────────────────────────────


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
    return str(resp.json()["id"])


# ── Start timer ───────────────────────────────────────────────────────────────


async def test_start_timer_returns_201(auth_client: AsyncClient) -> None:
    task_id = await _create_task(auth_client)
    resp = await auth_client.post("/time-entries/start", json={"task_id": task_id})
    assert resp.status_code == 201
    body = resp.json()
    assert body["task_id"] == task_id
    assert body["ended_at"] is None
    assert body["duration_seconds"] is None
    assert "id" in body
    assert "started_at" in body


# ── Stop timer ────────────────────────────────────────────────────────────────


async def test_stop_timer_sets_ended_at_and_duration(auth_client: AsyncClient) -> None:
    task_id = await _create_task(auth_client)
    start_resp = await auth_client.post(
        "/time-entries/start", json={"task_id": task_id}
    )
    entry_id = start_resp.json()["id"]

    stop_resp = await auth_client.post(f"/time-entries/{entry_id}/stop")
    assert stop_resp.status_code == 200
    body = stop_resp.json()
    assert body["ended_at"] is not None
    assert body["duration_seconds"] is not None
    assert body["duration_seconds"] >= 0


async def test_stop_already_stopped_timer_returns_409(
    auth_client: AsyncClient,
) -> None:
    task_id = await _create_task(auth_client)
    start_resp = await auth_client.post(
        "/time-entries/start", json={"task_id": task_id}
    )
    entry_id = start_resp.json()["id"]

    await auth_client.post(f"/time-entries/{entry_id}/stop")
    resp = await auth_client.post(f"/time-entries/{entry_id}/stop")
    assert resp.status_code == 409


async def test_stop_nonexistent_entry_returns_404(auth_client: AsyncClient) -> None:
    resp = await auth_client.post(f"/time-entries/{uuid.uuid4()}/stop")
    assert resp.status_code == 404


# ── Concurrency constraint ────────────────────────────────────────────────────


async def test_start_second_timer_returns_409(auth_client: AsyncClient) -> None:
    """Only one active timer allowed per user."""
    task_id = await _create_task(auth_client)
    await auth_client.post("/time-entries/start", json={"task_id": task_id})
    resp = await auth_client.post("/time-entries/start", json={"task_id": task_id})
    assert resp.status_code == 409


# ── List ──────────────────────────────────────────────────────────────────────


async def test_list_time_entries(auth_client: AsyncClient) -> None:
    task_id = await _create_task(auth_client)
    start_resp = await auth_client.post(
        "/time-entries/start", json={"task_id": task_id}
    )
    entry_id = start_resp.json()["id"]
    await auth_client.post(f"/time-entries/{entry_id}/stop")

    resp = await auth_client.get("/time-entries")
    assert resp.status_code == 200
    ids = [e["id"] for e in resp.json()]
    assert entry_id in ids


async def test_list_time_entries_filter_by_task_id(auth_client: AsyncClient) -> None:
    """Entries for task_a must not appear when filtering by task_b."""
    task_a = await _create_task(auth_client)
    task_b = await _create_task(auth_client)

    start_a = await auth_client.post("/time-entries/start", json={"task_id": task_a})
    entry_a_id = start_a.json()["id"]
    await auth_client.post(f"/time-entries/{entry_a_id}/stop")

    start_b = await auth_client.post("/time-entries/start", json={"task_id": task_b})
    entry_b_id = start_b.json()["id"]
    await auth_client.post(f"/time-entries/{entry_b_id}/stop")

    resp = await auth_client.get(f"/time-entries?task_id={task_b}")
    assert resp.status_code == 200
    ids = [e["id"] for e in resp.json()]
    assert entry_b_id in ids
    assert entry_a_id not in ids


# ── Delete ────────────────────────────────────────────────────────────────────


async def test_delete_time_entry_returns_204(auth_client: AsyncClient) -> None:
    task_id = await _create_task(auth_client)
    start_resp = await auth_client.post(
        "/time-entries/start", json={"task_id": task_id}
    )
    entry_id = start_resp.json()["id"]
    await auth_client.post(f"/time-entries/{entry_id}/stop")

    resp = await auth_client.delete(f"/time-entries/{entry_id}")
    assert resp.status_code == 204

    # Confirm gone via list
    list_resp = await auth_client.get("/time-entries")
    ids = [e["id"] for e in list_resp.json()]
    assert entry_id not in ids


# ── Ownership scoping ────────────────────────────────────────────────────────


async def test_other_user_entry_stop_returns_404(
    auth_client: AsyncClient, other_auth_client: AsyncClient
) -> None:
    """User B cannot stop User A's timer."""
    task_id = await _create_task(auth_client)
    start_resp = await auth_client.post(
        "/time-entries/start", json={"task_id": task_id}
    )
    entry_id = start_resp.json()["id"]

    resp = await other_auth_client.post(f"/time-entries/{entry_id}/stop")
    assert resp.status_code == 404
