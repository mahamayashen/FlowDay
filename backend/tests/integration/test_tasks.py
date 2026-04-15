from __future__ import annotations

from httpx import AsyncClient

# ── Helpers ───────────────────────────────────────────────────────────────────


async def _create_project(client: AsyncClient) -> str:
    """Create a project and return its ID."""
    resp = await client.post(
        "/projects", json={"name": "Task Host", "color": "#ABCDEF"}
    )
    assert resp.status_code == 201
    project_id: str = resp.json()["id"]
    return project_id


# ── Create ────────────────────────────────────────────────────────────────────


async def test_create_task_returns_201(auth_client: AsyncClient) -> None:
    project_id = await _create_project(auth_client)
    resp = await auth_client.post(
        f"/projects/{project_id}/tasks",
        json={"title": "Write tests", "priority": "high"},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["title"] == "Write tests"
    assert body["priority"] == "high"
    assert body["status"] == "todo"


# ── List ──────────────────────────────────────────────────────────────────────


async def test_list_tasks_for_project(auth_client: AsyncClient) -> None:
    project_id = await _create_project(auth_client)
    await auth_client.post(f"/projects/{project_id}/tasks", json={"title": "Task 1"})
    await auth_client.post(f"/projects/{project_id}/tasks", json={"title": "Task 2"})

    resp = await auth_client.get(f"/projects/{project_id}/tasks")
    assert resp.status_code == 200
    titles = [t["title"] for t in resp.json()]
    assert "Task 1" in titles
    assert "Task 2" in titles


# ── Get ───────────────────────────────────────────────────────────────────────


async def test_get_task_by_id(auth_client: AsyncClient) -> None:
    project_id = await _create_project(auth_client)
    create_resp = await auth_client.post(
        f"/projects/{project_id}/tasks", json={"title": "Find Me"}
    )
    task_id = create_resp.json()["id"]

    resp = await auth_client.get(f"/projects/{project_id}/tasks/{task_id}")
    assert resp.status_code == 200
    assert resp.json()["title"] == "Find Me"


# ── Update ────────────────────────────────────────────────────────────────────


async def test_update_task_status_to_done_sets_completed_at(
    auth_client: AsyncClient,
) -> None:
    project_id = await _create_project(auth_client)
    create_resp = await auth_client.post(
        f"/projects/{project_id}/tasks", json={"title": "Finish Me"}
    )
    task_id = create_resp.json()["id"]
    assert create_resp.json()["completed_at"] is None

    resp = await auth_client.patch(
        f"/projects/{project_id}/tasks/{task_id}", json={"status": "done"}
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "done"
    assert resp.json()["completed_at"] is not None


async def test_update_task_back_to_todo_clears_completed_at(
    auth_client: AsyncClient,
) -> None:
    """Mark done then back to todo — completed_at must be cleared."""
    project_id = await _create_project(auth_client)
    create_resp = await auth_client.post(
        f"/projects/{project_id}/tasks", json={"title": "Round Trip"}
    )
    task_id = create_resp.json()["id"]

    # Mark done
    await auth_client.patch(
        f"/projects/{project_id}/tasks/{task_id}", json={"status": "done"}
    )

    # Mark back to todo
    resp = await auth_client.patch(
        f"/projects/{project_id}/tasks/{task_id}", json={"status": "todo"}
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "todo"
    assert resp.json()["completed_at"] is None


# ── Delete ────────────────────────────────────────────────────────────────────


async def test_delete_task_returns_204(auth_client: AsyncClient) -> None:
    project_id = await _create_project(auth_client)
    create_resp = await auth_client.post(
        f"/projects/{project_id}/tasks", json={"title": "Delete Me"}
    )
    task_id = create_resp.json()["id"]

    resp = await auth_client.delete(f"/projects/{project_id}/tasks/{task_id}")
    assert resp.status_code == 204

    get_resp = await auth_client.get(f"/projects/{project_id}/tasks/{task_id}")
    assert get_resp.status_code == 404


# ── Validation (422) ─────────────────────────────────────────────────────────


async def test_create_task_with_bad_priority_returns_422(
    auth_client: AsyncClient,
) -> None:
    project_id = await _create_project(auth_client)
    resp = await auth_client.post(
        f"/projects/{project_id}/tasks",
        json={"title": "Bad Priority", "priority": "super_urgent"},
    )
    assert resp.status_code == 422


async def test_create_task_with_bad_status_returns_422(
    auth_client: AsyncClient,
) -> None:
    project_id = await _create_project(auth_client)
    resp = await auth_client.post(
        f"/projects/{project_id}/tasks",
        json={"title": "Bad Status", "status": "cancelled"},
    )
    assert resp.status_code == 422


# ── Ownership scoping ────────────────────────────────────────────────────────


async def test_task_in_other_users_project_returns_404(
    auth_client: AsyncClient, other_auth_client: AsyncClient
) -> None:
    """User A cannot access tasks in User B's project."""
    project_id = await _create_project(other_auth_client)
    create_resp = await other_auth_client.post(
        f"/projects/{project_id}/tasks", json={"title": "Private Task"}
    )
    task_id = create_resp.json()["id"]

    resp = await auth_client.get(f"/projects/{project_id}/tasks/{task_id}")
    assert resp.status_code == 404


async def test_list_tasks_in_other_users_project_returns_404(
    auth_client: AsyncClient, other_auth_client: AsyncClient
) -> None:
    """Listing tasks in another user's project must return 404."""
    project_id = await _create_project(other_auth_client)

    resp = await auth_client.get(f"/projects/{project_id}/tasks")
    assert resp.status_code == 404
