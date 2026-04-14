from __future__ import annotations

import uuid
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException

from app.models.project import Project, ProjectStatus
from app.schemas.project import ProjectCreate, ProjectUpdate
from app.services.project_service import (
    create_project,
    delete_project,
    get_project,
    list_projects,
    update_project,
)

USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")
OTHER_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000002")
PROJECT_ID = uuid.UUID("00000000-0000-0000-0000-aaaaaaaaaaaa")


def _make_fake_project(
    project_id: uuid.UUID = PROJECT_ID,
    user_id: uuid.UUID = USER_ID,
    name: str = "Test Project",
    color: str = "#FF0000",
    status: ProjectStatus = ProjectStatus.ACTIVE,
) -> MagicMock:
    fake = MagicMock(spec=Project)
    fake.id = project_id
    fake.user_id = user_id
    fake.name = name
    fake.color = color
    fake.client_name = None
    fake.hourly_rate = None
    fake.status = status
    return fake


# ---------------------------------------------------------------------------
# create_project
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_project_returns_project() -> None:
    """create_project must add a project to the session and return it."""
    db = AsyncMock()
    data = ProjectCreate(name="Work", color="#00FF00")

    result = await create_project(db=db, user_id=USER_ID, data=data)

    assert isinstance(result, Project)
    assert result.name == "Work"
    assert result.color == "#00FF00"
    assert result.user_id == USER_ID
    db.add.assert_called_once()
    db.commit.assert_awaited_once()
    db.refresh.assert_awaited_once()


@pytest.mark.asyncio
async def test_create_project_with_optional_fields() -> None:
    """create_project must set optional fields when provided."""
    db = AsyncMock()
    data = ProjectCreate(
        name="Consulting",
        color="#0000FF",
        client_name="Acme",
        hourly_rate=Decimal("200.00"),
    )

    result = await create_project(db=db, user_id=USER_ID, data=data)

    assert result.client_name == "Acme"
    assert result.hourly_rate == Decimal("200.00")


# ---------------------------------------------------------------------------
# get_project
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_project_returns_project_for_owner() -> None:
    """get_project must return the project when user_id matches."""
    fake = _make_fake_project()
    db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = fake
    db.execute.return_value = mock_result

    result = await get_project(db=db, project_id=PROJECT_ID, user_id=USER_ID)

    assert result.id == PROJECT_ID


@pytest.mark.asyncio
async def test_get_project_queries_by_project_id() -> None:
    """get_project must query WHERE id == project_id (not !=)."""
    fake = _make_fake_project()
    db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = fake
    db.execute.return_value = mock_result

    await get_project(db=db, project_id=PROJECT_ID, user_id=USER_ID)

    # Verify the WHERE clause uses == (not !=)
    executed_stmt = db.execute.call_args[0][0]
    where_clause = str(executed_stmt.compile(compile_kwargs={"literal_binds": True}))
    assert "projects.id =" in where_clause
    assert "projects.id !=" not in where_clause


@pytest.mark.asyncio
async def test_get_project_raises_404_when_not_found() -> None:
    """get_project must raise 404 when project does not exist."""
    db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    db.execute.return_value = mock_result

    with pytest.raises(HTTPException) as exc_info:
        await get_project(db=db, project_id=PROJECT_ID, user_id=USER_ID)

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Project not found"


@pytest.mark.asyncio
async def test_get_project_raises_404_for_wrong_user() -> None:
    """get_project must raise 404 (not 403) to prevent ID enumeration."""
    fake = _make_fake_project(user_id=OTHER_USER_ID)
    db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = fake
    db.execute.return_value = mock_result

    with pytest.raises(HTTPException) as exc_info:
        await get_project(db=db, project_id=PROJECT_ID, user_id=USER_ID)

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Project not found"


# ---------------------------------------------------------------------------
# list_projects
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_projects_returns_user_projects() -> None:
    """list_projects must return only projects for the given user."""
    fake1 = _make_fake_project(name="P1")
    fake2 = _make_fake_project(name="P2")
    db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [fake1, fake2]
    db.execute.return_value = mock_result

    result = await list_projects(db=db, user_id=USER_ID)

    assert len(result) == 2


@pytest.mark.asyncio
async def test_list_projects_queries_by_user_id() -> None:
    """list_projects must query WHERE user_id == user_id (not !=)."""
    db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    db.execute.return_value = mock_result

    await list_projects(db=db, user_id=USER_ID)

    executed_stmt = db.execute.call_args[0][0]
    where_clause = str(executed_stmt.compile(compile_kwargs={"literal_binds": True}))
    assert "projects.user_id =" in where_clause
    assert "projects.user_id !=" not in where_clause


@pytest.mark.asyncio
async def test_list_projects_returns_empty_list() -> None:
    """list_projects must return empty list when user has no projects."""
    db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    db.execute.return_value = mock_result

    result = await list_projects(db=db, user_id=USER_ID)

    assert result == []


# ---------------------------------------------------------------------------
# update_project
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_update_project_applies_changes() -> None:
    """update_project must apply only the provided fields."""
    fake = _make_fake_project()
    db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = fake
    db.execute.return_value = mock_result

    data = ProjectUpdate(name="Updated Name")
    result = await update_project(
        db=db, project_id=PROJECT_ID, user_id=USER_ID, data=data
    )

    assert result.name == "Updated Name"
    db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_update_project_only_sets_provided_fields() -> None:
    """update_project must use exclude_unset=True to skip unset fields."""
    fake = _make_fake_project()
    fake.name = "Original"
    fake.color = "#FF0000"
    fake.client_name = "OldClient"
    db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = fake
    db.execute.return_value = mock_result

    # Only update name — color, client_name, etc. should NOT be touched
    data = ProjectUpdate(name="NewName")
    await update_project(db=db, project_id=PROJECT_ID, user_id=USER_ID, data=data)

    # name was set, but color and client_name should remain unchanged
    assert fake.name == "NewName"
    assert fake.color == "#FF0000"
    assert fake.client_name == "OldClient"


@pytest.mark.asyncio
async def test_update_project_raises_404_for_wrong_user() -> None:
    """update_project must raise 404 (not 403) to prevent ID enumeration."""
    fake = _make_fake_project(user_id=OTHER_USER_ID)
    db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = fake
    db.execute.return_value = mock_result

    with pytest.raises(HTTPException) as exc_info:
        await update_project(
            db=db,
            project_id=PROJECT_ID,
            user_id=USER_ID,
            data=ProjectUpdate(name="X"),
        )

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Project not found"


@pytest.mark.asyncio
async def test_update_project_raises_404_when_not_found() -> None:
    """update_project must raise 404 when project does not exist."""
    db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    db.execute.return_value = mock_result

    with pytest.raises(HTTPException) as exc_info:
        await update_project(
            db=db,
            project_id=PROJECT_ID,
            user_id=USER_ID,
            data=ProjectUpdate(name="X"),
        )

    assert exc_info.value.status_code == 404


# ---------------------------------------------------------------------------
# delete_project
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_delete_project_removes_project() -> None:
    """delete_project must delete the project from the database."""
    fake = _make_fake_project()
    db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = fake
    db.execute.return_value = mock_result

    await delete_project(db=db, project_id=PROJECT_ID, user_id=USER_ID)

    db.delete.assert_awaited_once_with(fake)
    db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_delete_project_raises_404_for_wrong_user() -> None:
    """delete_project must raise 404 (not 403) to prevent ID enumeration."""
    fake = _make_fake_project(user_id=OTHER_USER_ID)
    db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = fake
    db.execute.return_value = mock_result

    with pytest.raises(HTTPException) as exc_info:
        await delete_project(db=db, project_id=PROJECT_ID, user_id=USER_ID)

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Project not found"


@pytest.mark.asyncio
async def test_delete_project_raises_404_when_not_found() -> None:
    """delete_project must raise 404 when project does not exist."""
    db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    db.execute.return_value = mock_result

    with pytest.raises(HTTPException) as exc_info:
        await delete_project(db=db, project_id=PROJECT_ID, user_id=USER_ID)

    assert exc_info.value.status_code == 404
