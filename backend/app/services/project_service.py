from __future__ import annotations

import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project
from app.schemas.project import ProjectCreate, ProjectUpdate


async def create_project(
    db: AsyncSession, user_id: uuid.UUID, data: ProjectCreate
) -> Project:
    """Create a new project owned by user_id."""
    project = Project(
        user_id=user_id,
        name=data.name,
        color=data.color,
        client_name=data.client_name,
        hourly_rate=data.hourly_rate,
    )
    db.add(project)
    await db.commit()
    await db.refresh(project)
    return project


async def _get_project_or_404(db: AsyncSession, project_id: uuid.UUID) -> Project:
    """Fetch a project by ID or raise 404."""
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )
    return project


def _check_ownership(project: Project, user_id: uuid.UUID) -> None:
    """Raise 404 if the project does not belong to user_id.

    Returns 404 (not 403) to avoid revealing that a project with this
    ID exists but belongs to another user (prevents ID enumeration).
    """
    if project.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )


async def get_project(
    db: AsyncSession, project_id: uuid.UUID, user_id: uuid.UUID
) -> Project:
    """Get a single project, enforcing ownership."""
    project = await _get_project_or_404(db, project_id)
    _check_ownership(project, user_id)
    return project


async def list_projects(
    db: AsyncSession,
    user_id: uuid.UUID,
    *,
    skip: int = 0,
    limit: int = 50,
) -> list[Project]:
    """List projects for a given user with pagination."""
    stmt = select(Project).where(Project.user_id == user_id).offset(skip).limit(limit)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def update_project(
    db: AsyncSession,
    project_id: uuid.UUID,
    user_id: uuid.UUID,
    data: ProjectUpdate,
) -> Project:
    """Update a project, enforcing ownership. Only set provided fields."""
    project = await _get_project_or_404(db, project_id)
    _check_ownership(project, user_id)

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(project, field, value)

    await db.commit()
    await db.refresh(project)
    return project


async def delete_project(
    db: AsyncSession, project_id: uuid.UUID, user_id: uuid.UUID
) -> None:
    """Delete a project, enforcing ownership."""
    project = await _get_project_or_404(db, project_id)
    _check_ownership(project, user_id)
    await db.delete(project)
    await db.commit()
