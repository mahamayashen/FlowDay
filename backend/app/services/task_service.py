from __future__ import annotations

import uuid
from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.task import Task, TaskStatus
from app.schemas.task import TaskCreate, TaskUpdate
from app.services.project_service import get_project


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


async def _get_task_or_404(db: AsyncSession, task_id: uuid.UUID) -> Task:
    """Fetch a task by ID or raise 404."""
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()
    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )
    return task


def _check_task_project(task: Task, project_id: uuid.UUID) -> None:
    """Raise 404 if the task does not belong to the given project."""
    if task.project_id != project_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )


async def get_task(
    db: AsyncSession,
    task_id: uuid.UUID,
    project_id: uuid.UUID,
    user_id: uuid.UUID,
) -> Task:
    """Get a single task, enforcing project ownership."""
    await get_project(db, project_id, user_id)
    task = await _get_task_or_404(db, task_id)
    _check_task_project(task, project_id)
    return task


async def list_tasks(
    db: AsyncSession,
    project_id: uuid.UUID,
    user_id: uuid.UUID,
    *,
    skip: int = 0,
    limit: int = 50,
) -> list[Task]:
    """List tasks for a given project with pagination."""
    await get_project(db, project_id, user_id)
    stmt = (
        select(Task)
        .where(Task.project_id == project_id)
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def update_task(
    db: AsyncSession,
    task_id: uuid.UUID,
    project_id: uuid.UUID,
    user_id: uuid.UUID,
    data: TaskUpdate,
) -> Task:
    """Update a task, enforcing project ownership. Only set provided fields."""
    await get_project(db, project_id, user_id)
    task = await _get_task_or_404(db, task_id)
    _check_task_project(task, project_id)

    updates = data.model_dump(exclude_unset=True)

    if "status" in updates:
        if updates["status"] == TaskStatus.DONE:
            task.completed_at = datetime.now(UTC)
        else:
            task.completed_at = None

    for field, value in updates.items():
        setattr(task, field, value)

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
    await get_project(db, project_id, user_id)
    task = await _get_task_or_404(db, task_id)
    _check_task_project(task, project_id)
    await db.delete(task)
    await db.commit()
