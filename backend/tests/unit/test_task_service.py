from __future__ import annotations

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from app.models.task import Task
from app.schemas.task import TaskCreate, TaskUpdate
from app.services.task_service import (
    create_task,
    delete_task,
    get_task,
    list_tasks,
    update_task,
)

USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")
OTHER_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000002")
PROJECT_ID = uuid.UUID("00000000-0000-0000-0000-aaaaaaaaaaaa")
TASK_ID = uuid.UUID("00000000-0000-0000-0000-bbbbbbbbbbbb")


def _make_fake_task(
    task_id: uuid.UUID = TASK_ID,
    project_id: uuid.UUID = PROJECT_ID,
    title: str = "Test Task",
    status: str = "todo",
    completed_at: datetime | None = None,
) -> MagicMock:
    fake = MagicMock(spec=Task)
    fake.id = task_id
    fake.project_id = project_id
    fake.title = title
    fake.description = None
    fake.estimate_minutes = None
    fake.priority = "medium"
    fake.status = status
    fake.due_date = None
    fake.created_at = datetime.now(UTC)
    fake.completed_at = completed_at
    return fake


def _mock_db_returning(obj: object) -> AsyncMock:
    """Create a mocked AsyncSession whose execute returns obj via scalar_one_or_none."""
    db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = obj
    db.execute.return_value = mock_result
    return db


# ---------------------------------------------------------------------------
# create_task  (still uses get_project for ownership before INSERT)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@patch("app.services.task_service.get_project", new_callable=AsyncMock)
async def test_create_task_returns_task(mock_get_project: AsyncMock) -> None:
    """create_task must add a task to the session and return it."""
    db = AsyncMock()
    data = TaskCreate(title="Write tests")

    result = await create_task(db=db, project_id=PROJECT_ID, user_id=USER_ID, data=data)

    assert isinstance(result, Task)
    assert result.title == "Write tests"
    assert result.project_id == PROJECT_ID
    db.add.assert_called_once()
    db.commit.assert_awaited_once()
    db.refresh.assert_awaited_once()


@pytest.mark.asyncio
@patch("app.services.task_service.get_project", new_callable=AsyncMock)
async def test_create_task_with_optional_fields(mock_get_project: AsyncMock) -> None:
    """create_task must set optional fields when provided."""
    db = AsyncMock()
    data = TaskCreate(
        title="Work",
        description="Some description",
        estimate_minutes=60,
        priority="high",
    )

    result = await create_task(db=db, project_id=PROJECT_ID, user_id=USER_ID, data=data)

    assert result.description == "Some description"
    assert result.estimate_minutes == 60
    assert result.priority == "high"


@pytest.mark.asyncio
@patch("app.services.task_service.get_project", new_callable=AsyncMock)
async def test_create_task_verifies_project_ownership(
    mock_get_project: AsyncMock,
) -> None:
    """create_task must call get_project to verify project ownership."""
    db = AsyncMock()
    data = TaskCreate(title="Work")

    await create_task(db=db, project_id=PROJECT_ID, user_id=USER_ID, data=data)

    mock_get_project.assert_awaited_once_with(db, PROJECT_ID, USER_ID)


@pytest.mark.asyncio
@patch("app.services.task_service.get_project", new_callable=AsyncMock)
async def test_create_task_raises_404_for_wrong_project_owner(
    mock_get_project: AsyncMock,
) -> None:
    """create_task must propagate 404 when project ownership fails."""
    mock_get_project.side_effect = HTTPException(
        status_code=404, detail="Project not found"
    )
    db = AsyncMock()
    data = TaskCreate(title="Work")

    with pytest.raises(HTTPException) as exc_info:
        await create_task(db=db, project_id=PROJECT_ID, user_id=USER_ID, data=data)

    assert exc_info.value.status_code == 404


# ---------------------------------------------------------------------------
# get_task  (uses _get_task_with_ownership — single joined query)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_task_returns_task_for_owner() -> None:
    """get_task must return the task when joined ownership query succeeds."""
    fake = _make_fake_task()
    db = _mock_db_returning(fake)

    result = await get_task(
        db=db, task_id=TASK_ID, project_id=PROJECT_ID, user_id=USER_ID
    )

    assert result.id == TASK_ID


@pytest.mark.asyncio
async def test_get_task_raises_404_when_not_found() -> None:
    """get_task must raise 404 when task does not exist."""
    db = _mock_db_returning(None)

    with pytest.raises(HTTPException) as exc_info:
        await get_task(db=db, task_id=TASK_ID, project_id=PROJECT_ID, user_id=USER_ID)

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Task not found"


@pytest.mark.asyncio
async def test_get_task_raises_404_for_wrong_project_owner() -> None:
    """get_task must raise 404 when user doesn't own the project (joined query)."""
    db = _mock_db_returning(None)  # join fails → no result

    with pytest.raises(HTTPException) as exc_info:
        await get_task(
            db=db, task_id=TASK_ID, project_id=PROJECT_ID, user_id=OTHER_USER_ID
        )

    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_get_task_query_joins_project_for_ownership() -> None:
    """get_task must use a joined query that checks task_id, project_id, and user_id."""
    fake = _make_fake_task()
    db = _mock_db_returning(fake)

    await get_task(db=db, task_id=TASK_ID, project_id=PROJECT_ID, user_id=USER_ID)

    executed_stmt = db.execute.call_args[0][0]
    compiled = str(executed_stmt.compile(compile_kwargs={"literal_binds": True}))
    assert "tasks.id =" in compiled
    assert "tasks.id !=" not in compiled
    assert "tasks.project_id =" in compiled
    assert "projects.user_id =" in compiled
    assert "JOIN" in compiled.upper()


@pytest.mark.asyncio
async def test_get_task_raises_404_for_wrong_project() -> None:
    """get_task must raise 404 if task belongs to a different project."""
    db = _mock_db_returning(None)  # project_id mismatch → no result

    with pytest.raises(HTTPException) as exc_info:
        await get_task(db=db, task_id=TASK_ID, project_id=PROJECT_ID, user_id=USER_ID)

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Task not found"


# ---------------------------------------------------------------------------
# list_tasks  (still uses get_project for ownership before SELECT)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@patch("app.services.task_service.get_project", new_callable=AsyncMock)
async def test_list_tasks_returns_project_tasks(mock_get_project: AsyncMock) -> None:
    """list_tasks must return tasks for the given project."""
    fake1 = _make_fake_task(title="T1")
    fake2 = _make_fake_task(title="T2")
    db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [fake1, fake2]
    db.execute.return_value = mock_result

    result = await list_tasks(db=db, project_id=PROJECT_ID, user_id=USER_ID)

    assert len(result) == 2


@pytest.mark.asyncio
@patch("app.services.task_service.get_project", new_callable=AsyncMock)
async def test_list_tasks_queries_by_project_id(mock_get_project: AsyncMock) -> None:
    """list_tasks must query WHERE project_id == project_id (not !=)."""
    db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    db.execute.return_value = mock_result

    await list_tasks(db=db, project_id=PROJECT_ID, user_id=USER_ID)

    executed_stmt = db.execute.call_args[0][0]
    where_clause = str(executed_stmt.compile(compile_kwargs={"literal_binds": True}))
    assert "tasks.project_id =" in where_clause
    assert "tasks.project_id !=" not in where_clause


@pytest.mark.asyncio
@patch("app.services.task_service.get_project", new_callable=AsyncMock)
async def test_list_tasks_returns_empty_list(mock_get_project: AsyncMock) -> None:
    """list_tasks must return empty list when project has no tasks."""
    db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    db.execute.return_value = mock_result

    result = await list_tasks(db=db, project_id=PROJECT_ID, user_id=USER_ID)

    assert result == []


@pytest.mark.asyncio
@patch("app.services.task_service.get_project", new_callable=AsyncMock)
async def test_list_tasks_applies_pagination(mock_get_project: AsyncMock) -> None:
    """list_tasks must apply offset and limit to the query."""
    db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    db.execute.return_value = mock_result

    await list_tasks(db=db, project_id=PROJECT_ID, user_id=USER_ID, skip=10, limit=5)

    executed_stmt = db.execute.call_args[0][0]
    compiled = str(executed_stmt.compile(compile_kwargs={"literal_binds": True}))
    assert "LIMIT" in compiled.upper()
    assert "OFFSET" in compiled.upper()


@pytest.mark.asyncio
@patch("app.services.task_service.get_project", new_callable=AsyncMock)
async def test_list_tasks_verifies_project_ownership(
    mock_get_project: AsyncMock,
) -> None:
    """list_tasks must call get_project to verify project ownership."""
    db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    db.execute.return_value = mock_result

    await list_tasks(db=db, project_id=PROJECT_ID, user_id=USER_ID)

    mock_get_project.assert_awaited_once_with(db, PROJECT_ID, USER_ID)


# ---------------------------------------------------------------------------
# update_task  (uses _get_task_with_ownership — single joined query)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_update_task_applies_changes() -> None:
    """update_task must apply only the provided fields."""
    fake = _make_fake_task()
    db = _mock_db_returning(fake)

    data = TaskUpdate(title="Updated Title")
    result = await update_task(
        db=db, task_id=TASK_ID, project_id=PROJECT_ID, user_id=USER_ID, data=data
    )

    assert result.title == "Updated Title"
    db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_update_task_only_sets_provided_fields() -> None:
    """update_task must use exclude_unset=True to skip unset fields."""
    fake = _make_fake_task()
    fake.title = "Original"
    fake.description = "Old desc"
    db = _mock_db_returning(fake)

    data = TaskUpdate(title="NewTitle")
    await update_task(
        db=db, task_id=TASK_ID, project_id=PROJECT_ID, user_id=USER_ID, data=data
    )

    assert fake.title == "NewTitle"
    assert fake.description == "Old desc"


@pytest.mark.asyncio
async def test_update_task_sets_completed_at_on_done() -> None:
    """update_task must set completed_at when status changes to done."""
    fake = _make_fake_task(status="todo")
    fake.completed_at = None
    db = _mock_db_returning(fake)

    data = TaskUpdate(status="done")
    await update_task(
        db=db, task_id=TASK_ID, project_id=PROJECT_ID, user_id=USER_ID, data=data
    )

    assert fake.completed_at is not None


@pytest.mark.asyncio
async def test_update_task_clears_completed_at_on_status_change() -> None:
    """update_task must clear completed_at when status changes away from done."""
    fake = _make_fake_task(status="done", completed_at=datetime.now(UTC))
    db = _mock_db_returning(fake)

    data = TaskUpdate(status="todo")
    await update_task(
        db=db, task_id=TASK_ID, project_id=PROJECT_ID, user_id=USER_ID, data=data
    )

    assert fake.completed_at is None


@pytest.mark.asyncio
async def test_update_task_completed_at_wins_over_setattr_loop() -> None:
    """completed_at must be set AFTER the setattr loop so the service value wins."""
    fake = _make_fake_task(status="todo")
    fake.completed_at = None
    db = _mock_db_returning(fake)

    data = TaskUpdate(status="done")
    await update_task(
        db=db, task_id=TASK_ID, project_id=PROJECT_ID, user_id=USER_ID, data=data
    )

    # completed_at must be a real datetime, not None — proving service logic runs last
    assert isinstance(fake.completed_at, datetime)


@pytest.mark.asyncio
async def test_update_task_raises_404_when_not_found() -> None:
    """update_task must raise 404 when task does not exist."""
    db = _mock_db_returning(None)

    with pytest.raises(HTTPException) as exc_info:
        await update_task(
            db=db,
            task_id=TASK_ID,
            project_id=PROJECT_ID,
            user_id=USER_ID,
            data=TaskUpdate(title="X"),
        )

    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_update_task_query_joins_for_ownership() -> None:
    """update_task must verify ownership via joined query."""
    fake = _make_fake_task()
    db = _mock_db_returning(fake)

    await update_task(
        db=db,
        task_id=TASK_ID,
        project_id=PROJECT_ID,
        user_id=USER_ID,
        data=TaskUpdate(title="X"),
    )

    executed_stmt = db.execute.call_args[0][0]
    compiled = str(executed_stmt.compile(compile_kwargs={"literal_binds": True}))
    assert "projects.user_id =" in compiled
    assert "JOIN" in compiled.upper()


@pytest.mark.asyncio
async def test_update_task_raises_404_for_wrong_project() -> None:
    """update_task must raise 404 if task doesn't belong to project."""
    db = _mock_db_returning(None)

    with pytest.raises(HTTPException) as exc_info:
        await update_task(
            db=db,
            task_id=TASK_ID,
            project_id=PROJECT_ID,
            user_id=USER_ID,
            data=TaskUpdate(title="X"),
        )

    assert exc_info.value.status_code == 404


# ---------------------------------------------------------------------------
# delete_task  (uses _get_task_with_ownership — single joined query)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_delete_task_removes_task() -> None:
    """delete_task must delete the task from the database."""
    fake = _make_fake_task()
    db = _mock_db_returning(fake)

    await delete_task(db=db, task_id=TASK_ID, project_id=PROJECT_ID, user_id=USER_ID)

    db.delete.assert_awaited_once_with(fake)
    db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_delete_task_raises_404_when_not_found() -> None:
    """delete_task must raise 404 when task does not exist."""
    db = _mock_db_returning(None)

    with pytest.raises(HTTPException) as exc_info:
        await delete_task(
            db=db, task_id=TASK_ID, project_id=PROJECT_ID, user_id=USER_ID
        )

    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_delete_task_query_joins_for_ownership() -> None:
    """delete_task must verify ownership via joined query."""
    fake = _make_fake_task()
    db = _mock_db_returning(fake)

    await delete_task(db=db, task_id=TASK_ID, project_id=PROJECT_ID, user_id=USER_ID)

    executed_stmt = db.execute.call_args[0][0]
    compiled = str(executed_stmt.compile(compile_kwargs={"literal_binds": True}))
    assert "projects.user_id =" in compiled
    assert "JOIN" in compiled.upper()


@pytest.mark.asyncio
async def test_delete_task_raises_404_for_wrong_project() -> None:
    """delete_task must raise 404 if task doesn't belong to project."""
    db = _mock_db_returning(None)

    with pytest.raises(HTTPException) as exc_info:
        await delete_task(
            db=db, task_id=TASK_ID, project_id=PROJECT_ID, user_id=USER_ID
        )

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Task not found"


# ---------------------------------------------------------------------------
# Mutation-killing tests for default parameters
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@patch("app.services.task_service.get_project", new_callable=AsyncMock)
async def test_list_tasks_default_skip_is_zero(
    mock_get_project: AsyncMock,
) -> None:
    """list_tasks default skip must be 0 (not 1)."""
    db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    db.execute.return_value = mock_result

    await list_tasks(db=db, project_id=PROJECT_ID, user_id=USER_ID)

    executed_stmt = db.execute.call_args[0][0]
    compiled = str(executed_stmt.compile(compile_kwargs={"literal_binds": True}))
    assert "OFFSET 0" in compiled


@pytest.mark.asyncio
@patch("app.services.task_service.get_project", new_callable=AsyncMock)
async def test_list_tasks_default_limit_is_50(
    mock_get_project: AsyncMock,
) -> None:
    """list_tasks default limit must be 50 (not 51)."""
    db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    db.execute.return_value = mock_result

    await list_tasks(db=db, project_id=PROJECT_ID, user_id=USER_ID)

    executed_stmt = db.execute.call_args[0][0]
    compiled = str(executed_stmt.compile(compile_kwargs={"literal_binds": True}))
    assert "LIMIT 50" in compiled
