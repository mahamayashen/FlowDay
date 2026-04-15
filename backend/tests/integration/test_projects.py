from __future__ import annotations

import uuid

from httpx import AsyncClient

# ── Create ────────────────────────────────────────────────────────────────────


async def test_create_project_returns_201(auth_client: AsyncClient) -> None:
    resp = await auth_client.post(
        "/projects", json={"name": "My Project", "color": "#FF0000"}
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["name"] == "My Project"
    assert body["color"] == "#FF0000"
    assert "id" in body


# ── List ──────────────────────────────────────────────────────────────────────


async def test_list_projects_returns_owned_only(
    auth_client: AsyncClient, other_auth_client: AsyncClient
) -> None:
    """User A creates a project; User B's list must not include it."""
    await auth_client.post(
        "/projects", json={"name": "A's Project", "color": "#111111"}
    )
    await other_auth_client.post(
        "/projects", json={"name": "B's Project", "color": "#222222"}
    )

    resp_a = await auth_client.get("/projects")
    assert resp_a.status_code == 200
    names_a = [p["name"] for p in resp_a.json()]
    assert "A's Project" in names_a
    assert "B's Project" not in names_a

    resp_b = await other_auth_client.get("/projects")
    names_b = [p["name"] for p in resp_b.json()]
    assert "B's Project" in names_b
    assert "A's Project" not in names_b


# ── Get ───────────────────────────────────────────────────────────────────────


async def test_get_project_by_id(auth_client: AsyncClient) -> None:
    create_resp = await auth_client.post(
        "/projects", json={"name": "Fetch Me", "color": "#AABBCC"}
    )
    project_id = create_resp.json()["id"]

    resp = await auth_client.get(f"/projects/{project_id}")
    assert resp.status_code == 200
    assert resp.json()["name"] == "Fetch Me"


async def test_get_other_users_project_returns_404(
    auth_client: AsyncClient, other_auth_client: AsyncClient
) -> None:
    """Accessing another user's project must return 404 (not 403)."""
    create_resp = await other_auth_client.post(
        "/projects", json={"name": "Secret", "color": "#000000"}
    )
    project_id = create_resp.json()["id"]

    resp = await auth_client.get(f"/projects/{project_id}")
    assert resp.status_code == 404


async def test_get_nonexistent_project_returns_404(auth_client: AsyncClient) -> None:
    resp = await auth_client.get(f"/projects/{uuid.uuid4()}")
    assert resp.status_code == 404


# ── Update ────────────────────────────────────────────────────────────────────


async def test_update_project_name(auth_client: AsyncClient) -> None:
    create_resp = await auth_client.post(
        "/projects", json={"name": "Old Name", "color": "#123456"}
    )
    project_id = create_resp.json()["id"]

    resp = await auth_client.patch(f"/projects/{project_id}", json={"name": "New Name"})
    assert resp.status_code == 200
    assert resp.json()["name"] == "New Name"
    assert resp.json()["color"] == "#123456"  # unchanged


# ── Delete ────────────────────────────────────────────────────────────────────


async def test_delete_project_returns_204(auth_client: AsyncClient) -> None:
    create_resp = await auth_client.post(
        "/projects", json={"name": "Delete Me", "color": "#FFFFFF"}
    )
    project_id = create_resp.json()["id"]

    resp = await auth_client.delete(f"/projects/{project_id}")
    assert resp.status_code == 204

    # Confirm it's gone
    get_resp = await auth_client.get(f"/projects/{project_id}")
    assert get_resp.status_code == 404
