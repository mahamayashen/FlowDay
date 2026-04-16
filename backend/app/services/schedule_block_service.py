from __future__ import annotations

import uuid
from datetime import date

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project
from app.models.schedule_block import ScheduleBlock
from app.models.task import Task
from app.schemas.schedule_block import ScheduleBlockCreate, ScheduleBlockUpdate


async def _get_block_with_ownership(
    db: AsyncSession,
    block_id: uuid.UUID,
    user_id: uuid.UUID,
) -> ScheduleBlock:
    """Fetch a schedule block verifying the user owns it via Task → Project.

    Returns 404 for missing block or ownership mismatch (prevents ID enumeration).
    """
    stmt = (
        select(ScheduleBlock)
        .join(Task, ScheduleBlock.task_id == Task.id)
        .join(Project, Task.project_id == Project.id)
        .where(
            ScheduleBlock.id == block_id,
            Project.user_id == user_id,
        )
    )
    result = await db.execute(stmt)
    block = result.scalar_one_or_none()
    if block is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Schedule block not found",
        )
    return block


async def _verify_task_ownership(
    db: AsyncSession,
    task_id: uuid.UUID,
    user_id: uuid.UUID,
) -> None:
    """Verify that the task exists and belongs to the user via Project."""
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


async def _check_overlap(
    db: AsyncSession,
    user_id: uuid.UUID,
    block_date: date,
    start_hour: object,
    end_hour: object,
    exclude_id: uuid.UUID | None = None,
) -> None:
    """Raise 409 if an overlapping block exists for the same user and date."""
    stmt = (
        select(ScheduleBlock)
        .join(Task, ScheduleBlock.task_id == Task.id)
        .join(Project, Task.project_id == Project.id)
        .where(
            Project.user_id == user_id,
            ScheduleBlock.date == block_date,
            ScheduleBlock.start_hour < end_hour,
            ScheduleBlock.end_hour > start_hour,
        )
    )
    if exclude_id is not None:
        stmt = stmt.where(ScheduleBlock.id != exclude_id)
    result = await db.execute(stmt)
    if result.scalars().first() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Schedule block overlaps with an existing block",
        )


async def create_schedule_block(
    db: AsyncSession,
    user_id: uuid.UUID,
    data: ScheduleBlockCreate,
) -> ScheduleBlock:
    """Create a new schedule block, verifying task ownership and no overlap."""
    await _verify_task_ownership(db, data.task_id, user_id)
    await _check_overlap(db, user_id, data.date, data.start_hour, data.end_hour)

    block = ScheduleBlock(
        task_id=data.task_id,
        date=data.date,
        start_hour=data.start_hour,
        end_hour=data.end_hour,
        source=data.source,
    )
    db.add(block)
    await db.commit()
    await db.refresh(block)
    return block


async def get_schedule_block(
    db: AsyncSession,
    block_id: uuid.UUID,
    user_id: uuid.UUID,
) -> ScheduleBlock:
    """Get a single schedule block, enforcing ownership."""
    return await _get_block_with_ownership(db, block_id, user_id)


async def list_schedule_blocks(
    db: AsyncSession,
    user_id: uuid.UUID,
    query_date: date,
) -> list[ScheduleBlock]:
    """List schedule blocks for a given user and date."""
    stmt = (
        select(ScheduleBlock)
        .join(Task, ScheduleBlock.task_id == Task.id)
        .join(Project, Task.project_id == Project.id)
        .where(
            Project.user_id == user_id,
            ScheduleBlock.date == query_date,
        )
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def update_schedule_block(
    db: AsyncSession,
    block_id: uuid.UUID,
    user_id: uuid.UUID,
    data: ScheduleBlockUpdate,
) -> ScheduleBlock:
    """Update a schedule block, enforcing ownership and overlap check."""
    block = await _get_block_with_ownership(db, block_id, user_id)

    updates = data.model_dump(exclude_unset=True)

    # Determine effective values for overlap check
    effective_date = updates.get("date", block.date)
    effective_start = updates.get("start_hour", block.start_hour)
    effective_end = updates.get("end_hour", block.end_hour)

    if effective_end <= effective_start:
        raise HTTPException(
            status_code=422,
            detail="end_hour must be greater than start_hour",
        )

    if "date" in updates or "start_hour" in updates or "end_hour" in updates:
        await _check_overlap(
            db,
            user_id,
            effective_date,
            effective_start,
            effective_end,
            exclude_id=block_id,
        )

    for field, value in updates.items():
        setattr(block, field, value)

    await db.commit()
    await db.refresh(block)
    return block


async def delete_schedule_block(
    db: AsyncSession,
    block_id: uuid.UUID,
    user_id: uuid.UUID,
) -> None:
    """Delete a schedule block, enforcing ownership."""
    block = await _get_block_with_ownership(db, block_id, user_id)
    await db.delete(block)
    await db.commit()
