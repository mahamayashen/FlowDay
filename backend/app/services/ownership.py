from __future__ import annotations

import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project
from app.models.task import Task


async def verify_task_ownership(
    db: AsyncSession,
    task_id: uuid.UUID,
    user_id: uuid.UUID,
) -> None:
    """Verify that the task exists and belongs to the user via Project.

    Returns 404 for missing task or ownership mismatch (prevents ID enumeration).
    """
    stmt = (
        select(Task)
        .join(Project, Task.project_id == Project.id)
        .where(
            Task.id == task_id,
            Project.user_id == user_id,
        )
    )
    result = await db.execute(stmt)
    if result.scalar_one_or_none() is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )
