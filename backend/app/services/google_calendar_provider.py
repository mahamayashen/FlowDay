from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.external_sync import ExternalSync
from app.models.project import Project
from app.models.schedule_block import ScheduleBlock, ScheduleBlockSource
from app.models.task import Task
from app.services.google_calendar import fetch_calendar_events, get_valid_access_token
from app.services.sync_provider import BaseSyncProvider, provider_registry

_SENTINEL_PROJECT_NAME = "Google Calendar"
_SENTINEL_PROJECT_COLOR = "#4285F4"
_SYNC_DAYS_AHEAD = 7


class GoogleCalendarSyncProvider(BaseSyncProvider):
    """Syncs Google Calendar events as ScheduleBlock rows (source=google_calendar)."""

    async def sync(self, db: AsyncSession, sync_record: ExternalSync) -> None:
        """Fetch calendar events and upsert them as schedule blocks."""
        access_token = await get_valid_access_token(db, sync_record)

        now = datetime.now(UTC)
        time_min = now.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
        time_max = (
            (now + timedelta(days=_SYNC_DAYS_AHEAD))
            .replace(hour=23, minute=59, second=59, microsecond=0)
            .isoformat()
        )

        events = await fetch_calendar_events(access_token, time_min, time_max)

        project = await _get_or_create_sentinel_project(db, sync_record.user_id)

        # Delete existing tasks + blocks (CASCADE) for the sentinel project
        sync_start = now.date()
        sync_end = (now + timedelta(days=_SYNC_DAYS_AHEAD)).date()
        await _delete_existing_tasks_and_blocks(
            db, sync_record.user_id, sync_start, sync_end
        )

        for event in events:
            block_data = _event_to_block_data(event)
            if block_data is None:
                continue  # skip all-day events
            task = Task(
                project_id=project.id,
                title=event.get("summary") or "Google Calendar Event",
                description=event.get("id"),
            )
            db.add(task)
            await db.flush()

            block = ScheduleBlock(
                task_id=task.id,
                date=block_data["date"],
                start_hour=block_data["start_hour"],
                end_hour=block_data["end_hour"],
                source=ScheduleBlockSource.GOOGLE_CALENDAR,
            )
            db.add(block)

        await db.flush()


async def _get_or_create_sentinel_project(
    db: AsyncSession,
    user_id: Any,
) -> Project:
    """Return the user's Google Calendar sentinel project, creating it if needed."""
    result = await db.execute(
        select(Project).where(
            Project.user_id == user_id,
            Project.name == _SENTINEL_PROJECT_NAME,
        )
    )
    project = result.scalar_one_or_none()
    if project is None:
        project = Project(
            user_id=user_id,
            name=_SENTINEL_PROJECT_NAME,
            color=_SENTINEL_PROJECT_COLOR,
        )
        db.add(project)
        await db.flush()
    return project


async def _delete_existing_tasks_and_blocks(
    db: AsyncSession,
    user_id: Any,
    start: date,
    end: date,
) -> None:
    """Delete sentinel Tasks (and their ScheduleBlocks via CASCADE) in date range."""
    # Find task IDs that have google_calendar blocks in the date range
    task_ids_result = await db.execute(
        select(Task.id)
        .join(Project, Task.project_id == Project.id)
        .join(ScheduleBlock, ScheduleBlock.task_id == Task.id)
        .where(
            Project.user_id == user_id,
            Project.name == _SENTINEL_PROJECT_NAME,
            ScheduleBlock.source == ScheduleBlockSource.GOOGLE_CALENDAR,
            ScheduleBlock.date >= start,
            ScheduleBlock.date <= end,
        )
    )
    task_ids = [row[0] for row in task_ids_result.all()]
    if not task_ids:
        return

    # Deleting tasks cascades to their schedule blocks
    await db.execute(delete(Task).where(Task.id.in_(task_ids)))


def _event_to_block_data(
    event: dict[str, Any],
) -> dict[str, Any] | None:
    """Convert a Google Calendar event to block fields, or None for all-day events."""
    start_obj = event.get("start", {})
    end_obj = event.get("end", {})

    start_dt_str = start_obj.get("dateTime")
    end_dt_str = end_obj.get("dateTime")

    if not start_dt_str or not end_dt_str:
        return None  # all-day event — no hour information

    start_utc = datetime.fromisoformat(start_dt_str).astimezone(UTC)
    end_utc = datetime.fromisoformat(end_dt_str).astimezone(UTC)

    event_date = start_utc.date()
    start_hour = Decimal(str(round(start_utc.hour + start_utc.minute / 60, 2)))
    end_hour = Decimal(str(round(end_utc.hour + end_utc.minute / 60, 2)))

    if end_hour <= start_hour:
        end_hour = start_hour + Decimal("0.5")

    return {"date": event_date, "start_hour": start_hour, "end_hour": end_hour}


# Register with the global provider registry
provider_registry.register("google_calendar", GoogleCalendarSyncProvider)
