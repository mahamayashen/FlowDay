from __future__ import annotations

import uuid
from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project
from app.models.task import Task, TaskStatus
from app.schemas.task import TaskCreate, TaskUpdate
from app.services.project_service import get_project


async def _get_task_with_ownership(
    db: AsyncSession,
    task_id: uuid.UUID,
    project_id: uuid.UUID,
    user_id: uuid.UUID,
) -> Task:
    """Fetch a task verifying it belongs to the project and the user owns it.

    Uses a single joined query instead of separate project + task lookups.
    Returns 404 for missing task, missing project, or ownership mismatch
    (prevents ID enumeration).
    """
    stmt = (
        select(Task)
        .join(Project, Task.project_id == Project.id)
        .where(
            Task.id == task_id,
            Task.project_id == project_id,
            Project.user_id == user_id,
        )
    )
    result = await db.execute(stmt)
    task = result.scalar_one_or_none()
    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )
    return task


async def create_task(
    db: AsyncSession,
    project_id: uuid.UUID,
    user_id: uuid.UUID,
    data: TaskCreate,
) -> Task:
    """Create a new task under the given project, verifying ownership."""
    await get_project(db, project_id, user_id)

    task = Task(
        project_id=project_id,
        title=data.title,
        description=data.description,
        estimate_minutes=data.estimate_minutes,
        priority=data.priority,
        status=data.status,
        due_date=data.due_date,
    )
    db.add(task)
    await db.commit()
    await db.refresh(task)
    return task


async def get_task(
    db: AsyncSession,
    task_id: uuid.UUID,
    project_id: uuid.UUID,
    user_id: uuid.UUID,
) -> Task:
    """Get a single task, enforcing project ownership."""
    return await _get_task_with_ownership(db, task_id, project_id, user_id)


async def list_tasks(
    db: AsyncSession,
    project_id: uuid.UUID,
    user_id: uuid.UUID,
    *,
    skip: int = 0,
    limit: int = 50,
) -> list[Task]:
    """List tasks for a given project with pagination.

    Uses a single query with an EXISTS subquery to verify project ownership
    and fetch tasks in one round-trip.
    """
    ownership = (
        select(Project.id)
        .where(Project.id == project_id, Project.user_id == user_id)
        .exists()
    )
    stmt = (
        select(Task)
        .where(Task.project_id == project_id, ownership)
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(stmt)
    rows = list(result.scalars().all())
    if not rows:
        # Distinguish empty project from missing/unauthorized project.
        # If the EXISTS subquery matched, the project is valid — just has no tasks.
        check = await db.execute(
            select(
                select(Project.id)
                .where(Project.id == project_id, Project.user_id == user_id)
                .exists()
            )
        )
        if not check.scalar():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found",
            )
    return rows


async def update_task(
    db: AsyncSession,
    task_id: uuid.UUID,
    project_id: uuid.UUID,
    user_id: uuid.UUID,
    data: TaskUpdate,
) -> Task:
    """Update a task, enforcing project ownership. Only set provided fields."""
    task = await _get_task_with_ownership(db, task_id, project_id, user_id)

    updates = data.model_dump(exclude_unset=True)

    for field, value in updates.items():
        setattr(task, field, value)

    if "status" in updates:
        if TaskStatus(updates["status"]) == TaskStatus.DONE:
            task.completed_at = datetime.now(UTC)
        else:
            task.completed_at = None

    await db.commit()
    await db.refresh(task)
    return task


async def delete_task(
    db: AsyncSession,
    task_id: uuid.UUID,
    project_id: uuid.UUID,
    user_id: uuid.UUID,
) -> None:
    """Delete a task, enforcing project ownership."""
    task = await _get_task_with_ownership(db, task_id, project_id, user_id)
    await db.delete(task)
    await db.commit()
