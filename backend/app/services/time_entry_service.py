from __future__ import annotations

import uuid
from datetime import UTC, date, datetime, timedelta

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project
from app.models.task import Task
from app.models.time_entry import TimeEntry
from app.schemas.time_entry import TimeEntryStart


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


async def _check_no_active_timer(
    db: AsyncSession,
    user_id: uuid.UUID,
) -> None:
    """Raise 409 if the user already has an active (unstopped) timer."""
    stmt = (
        select(TimeEntry)
        .join(Task, TimeEntry.task_id == Task.id)
        .join(Project, Task.project_id == Project.id)
        .where(
            Project.user_id == user_id,
            TimeEntry.ended_at.is_(None),
        )
    )
    result = await db.execute(stmt)
    if result.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User already has an active timer",
        )


async def _get_entry_with_ownership(
    db: AsyncSession,
    entry_id: uuid.UUID,
    user_id: uuid.UUID,
) -> TimeEntry:
    """Fetch a time entry verifying the user owns it via Task -> Project."""
    stmt = (
        select(TimeEntry)
        .join(Task, TimeEntry.task_id == Task.id)
        .join(Project, Task.project_id == Project.id)
        .where(
            TimeEntry.id == entry_id,
            Project.user_id == user_id,
        )
    )
    result = await db.execute(stmt)
    entry = result.scalar_one_or_none()
    if entry is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Time entry not found",
        )
    return entry


async def start_timer(
    db: AsyncSession,
    user_id: uuid.UUID,
    data: TimeEntryStart,
) -> TimeEntry:
    """Start a new timer, verifying task ownership and no active timer."""
    await _verify_task_ownership(db, data.task_id, user_id)
    await _check_no_active_timer(db, user_id)

    entry = TimeEntry(
        task_id=data.task_id,
        started_at=data.started_at or datetime.now(UTC),
    )
    db.add(entry)
    await db.commit()
    await db.refresh(entry)
    return entry


async def stop_timer(
    db: AsyncSession,
    entry_id: uuid.UUID,
    user_id: uuid.UUID,
) -> TimeEntry:
    """Stop a running timer, computing duration_seconds."""
    entry = await _get_entry_with_ownership(db, entry_id, user_id)

    if entry.ended_at is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Timer already stopped",
        )

    now = datetime.now(UTC)
    entry.ended_at = now
    entry.duration_seconds = int((now - entry.started_at).total_seconds())
    await db.commit()
    await db.refresh(entry)
    return entry


async def list_time_entries(
    db: AsyncSession,
    user_id: uuid.UUID,
    task_id: uuid.UUID | None = None,
    query_date: date | None = None,
) -> list[TimeEntry]:
    """List time entries for the user with optional filters."""
    stmt = (
        select(TimeEntry)
        .join(Task, TimeEntry.task_id == Task.id)
        .join(Project, Task.project_id == Project.id)
        .where(Project.user_id == user_id)
    )

    if task_id is not None:
        stmt = stmt.where(TimeEntry.task_id == task_id)

    if query_date is not None:
        day_start = datetime(
            query_date.year, query_date.month, query_date.day, tzinfo=UTC
        )
        day_end = day_start + timedelta(days=1)
        stmt = stmt.where(
            TimeEntry.started_at >= day_start,
            TimeEntry.started_at < day_end,
        )

    result = await db.execute(stmt)
    return list(result.scalars().all())


async def delete_time_entry(
    db: AsyncSession,
    entry_id: uuid.UUID,
    user_id: uuid.UUID,
) -> None:
    """Delete a time entry, enforcing ownership."""
    entry = await _get_entry_with_ownership(db, entry_id, user_id)
    await db.delete(entry)
    await db.commit()
