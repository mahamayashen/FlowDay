from __future__ import annotations

import uuid

from sqlalchemy import inspect

from app.models.project import Project, ProjectStatus


def test_project_table_name_is_projects() -> None:
    """Project.__tablename__ must be 'projects'."""
    assert Project.__tablename__ == "projects"


def test_project_model_has_required_columns() -> None:
    """Project model must have all columns defined in DATA_MODEL.md."""
    columns = {c.name for c in inspect(Project).columns}
    expected = {
        "id",
        "user_id",
        "name",
        "color",
        "client_name",
        "hourly_rate",
        "status",
        "created_at",
    }
    assert expected.issubset(columns), f"Missing columns: {expected - columns}"


def test_project_id_is_uuid() -> None:
    """Project.id column type must be UUID."""
    col = inspect(Project).columns["id"]
    assert "UUID" in str(col.type).upper()


def test_project_user_id_is_foreign_key() -> None:
    """Project.user_id must reference users.id."""
    col = inspect(Project).columns["user_id"]
    fk_targets = {fk.target_fullname for fk in col.foreign_keys}
    assert "users.id" in fk_targets


def test_project_user_id_not_nullable() -> None:
    """Project.user_id must be NOT NULL."""
    col = inspect(Project).columns["user_id"]
    assert col.nullable is False


def test_project_name_not_nullable() -> None:
    """Project.name must be NOT NULL."""
    col = inspect(Project).columns["name"]
    assert col.nullable is False


def test_project_color_not_nullable() -> None:
    """Project.color must be NOT NULL."""
    col = inspect(Project).columns["color"]
    assert col.nullable is False


def test_project_client_name_nullable() -> None:
    """Project.client_name must be NULLABLE."""
    col = inspect(Project).columns["client_name"]
    assert col.nullable is True


def test_project_hourly_rate_nullable() -> None:
    """Project.hourly_rate must be NULLABLE."""
    col = inspect(Project).columns["hourly_rate"]
    assert col.nullable is True


def test_project_status_has_default() -> None:
    """Project.status column must have a default of ProjectStatus.ACTIVE."""
    col = inspect(Project).columns["status"]
    assert col.default is not None
    assert col.default.arg == ProjectStatus.ACTIVE


def test_project_status_enum_values() -> None:
    """ProjectStatus enum must have active and archived values."""
    assert ProjectStatus.ACTIVE.value == "active"
    assert ProjectStatus.ARCHIVED.value == "archived"


def test_project_repr_contains_name() -> None:
    """Project.__repr__ should include the project name for debugging."""
    p = Project(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        name="My Project",
        color="#FF0000",
    )
    assert "My Project" in repr(p)
