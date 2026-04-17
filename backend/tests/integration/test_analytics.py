from __future__ import annotations

from datetime import date, timedelta

from httpx import AsyncClient

# ── Helpers ───────────────────────────────────────────────────────────────────


async def _create_task(client: AsyncClient) -> tuple[str, str]:
    """Create a project and task, return (project_id, task_id)."""
    resp = await client.post(
        "/projects", json={"name": "Analytics Project", "color": "#123456"}
    )
    assert resp.status_code == 201
    project_id = resp.json()["id"]
    resp = await client.post(
        f"/projects/{project_id}/tasks", json={"title": "Analytics Task"}
    )
    assert resp.status_code == 201
    return project_id, resp.json()["id"]


def _today() -> str:
    return date.today().isoformat()


def _monday_of_week(d: date) -> str:
    return (d - timedelta(days=d.weekday())).isoformat()


# ── Planned-vs-actual ─────────────────────────────────────────────────────────


async def test_planned_vs_actual_with_data(auth_client: AsyncClient) -> None:
    """A schedule block + completed time entry on the same day produces a task row."""
    _, task_id = await _create_task(auth_client)
    today = _today()

    # Create schedule block (planned: 2 hours)
    await auth_client.post(
        "/schedule-blocks",
        json={"task_id": task_id, "date": today, "start_hour": 9.0, "end_hour": 11.0},
    )

    # Start and stop timer (actual: some seconds)
    start_resp = await auth_client.post(
        "/time-entries/start", json={"task_id": task_id}
    )
    entry_id = start_resp.json()["id"]
    await auth_client.post(f"/time-entries/{entry_id}/stop")

    resp = await auth_client.get(f"/analytics/planned-vs-actual?date={today}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["date"] == today
    task_ids = [t["task_id"] for t in body["tasks"]]
    assert task_id in task_ids

    task_row = next(t for t in body["tasks"] if t["task_id"] == task_id)
    assert task_row["planned_hours"] == 2.0
    assert task_row["status"] in ("done", "partial", "skipped")

    summary = body["summary"]
    assert summary["total_planned_hours"] >= 2.0


async def test_planned_vs_actual_empty_day(auth_client: AsyncClient) -> None:
    """A day with no data returns empty tasks and zero summary."""
    # Use a date in the past that has no data
    past_date = "2000-01-01"
    resp = await auth_client.get(f"/analytics/planned-vs-actual?date={past_date}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["tasks"] == []
    assert body["summary"]["total_planned_hours"] == 0.0
    assert body["summary"]["total_actual_hours"] == 0.0


async def test_planned_vs_actual_unplanned_work(auth_client: AsyncClient) -> None:
    """A time entry with no schedule block appears as UNPLANNED."""
    _, task_id = await _create_task(auth_client)

    # Start and stop timer (no schedule block)
    start_resp = await auth_client.post(
        "/time-entries/start", json={"task_id": task_id}
    )
    entry_id = start_resp.json()["id"]
    await auth_client.post(f"/time-entries/{entry_id}/stop")

    today = _today()
    resp = await auth_client.get(f"/analytics/planned-vs-actual?date={today}")
    assert resp.status_code == 200

    tasks = resp.json()["tasks"]
    task_ids = [t["task_id"] for t in tasks]
    assert task_id in task_ids

    task_row = next(t for t in tasks if t["task_id"] == task_id)
    assert task_row["status"] == "unplanned"
    assert task_row["planned_hours"] == 0.0


# ── Weekly stats ──────────────────────────────────────────────────────────────


async def test_weekly_stats_with_data(auth_client: AsyncClient) -> None:
    """Blocks and entries this week show up per project in weekly stats."""
    project_id, task_id = await _create_task(auth_client)
    today = date.today()
    monday = _monday_of_week(today)

    # Create a schedule block for today (2 planned hours)
    await auth_client.post(
        "/schedule-blocks",
        json={
            "task_id": task_id,
            "date": today.isoformat(),
            "start_hour": 13.0,
            "end_hour": 15.0,
        },
    )

    # Start and stop a timer
    start_resp = await auth_client.post(
        "/time-entries/start", json={"task_id": task_id}
    )
    entry_id = start_resp.json()["id"]
    await auth_client.post(f"/time-entries/{entry_id}/stop")

    resp = await auth_client.get(f"/analytics/weekly-stats?week_start={monday}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["week_start"] == monday

    project_ids = [p["project_id"] for p in body["projects"]]
    assert project_id in project_ids

    project_row = next(p for p in body["projects"] if p["project_id"] == project_id)
    assert project_row["planned_hours"] >= 2.0

    summary = body["summary"]
    assert summary["total_planned_hours"] >= 2.0


async def test_weekly_stats_empty_week(auth_client: AsyncClient) -> None:
    """A week with no data returns empty projects and zero summary."""
    resp = await auth_client.get("/analytics/weekly-stats?week_start=2000-01-03")
    assert resp.status_code == 200
    body = resp.json()
    assert body["projects"] == []
    assert body["summary"]["total_planned_hours"] == 0.0
    assert body["summary"]["total_actual_hours"] == 0.0


async def test_weekly_stats_auto_aligns_to_monday(auth_client: AsyncClient) -> None:
    """Passing a Wednesday aligns week_start to Monday in the response."""
    # Find the Wednesday of any week (e.g., 2024-06-19 is a Wednesday)
    wednesday = "2024-06-19"
    expected_monday = "2024-06-17"

    resp = await auth_client.get(f"/analytics/weekly-stats?week_start={wednesday}")
    assert resp.status_code == 200
    assert resp.json()["week_start"] == expected_monday
