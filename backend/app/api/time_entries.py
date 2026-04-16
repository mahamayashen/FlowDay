from __future__ import annotations

import uuid
from datetime import date

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.time_entry import TimeEntryResponse, TimeEntryStart
from app.services.time_entry_service import (
    delete_time_entry,
    list_time_entries,
    start_timer,
    stop_timer,
)

router = APIRouter(prefix="/time-entries", tags=["time-entries"])


@router.post(
    "/start",
    response_model=TimeEntryResponse,
    status_code=status.HTTP_201_CREATED,
)
async def start_timer_route(
    body: TimeEntryStart,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TimeEntryResponse:
    """Start a new timer for a task."""
    entry = await start_timer(db=db, user_id=current_user.id, data=body)
    return TimeEntryResponse.model_validate(entry)


@router.post("/{entry_id}/stop", response_model=TimeEntryResponse)
async def stop_timer_route(
    entry_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TimeEntryResponse:
    """Stop a running timer."""
    entry = await stop_timer(db=db, entry_id=entry_id, user_id=current_user.id)
    return TimeEntryResponse.model_validate(entry)


@router.get("", response_model=list[TimeEntryResponse])
async def list_time_entries_route(
    task_id: uuid.UUID | None = Query(default=None),
    entry_date: date | None = Query(default=None, alias="date"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[TimeEntryResponse]:
    """List time entries with optional filters."""
    entries = await list_time_entries(
        db=db, user_id=current_user.id, task_id=task_id, query_date=entry_date
    )
    return [TimeEntryResponse.model_validate(e) for e in entries]


@router.delete(
    "/{entry_id}", status_code=status.HTTP_204_NO_CONTENT, response_model=None
)
async def delete_time_entry_route(
    entry_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a time entry."""
    await delete_time_entry(db=db, entry_id=entry_id, user_id=current_user.id)
