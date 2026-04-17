from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.external_sync import ExternalSync, SyncStatus
from app.services.sync_provider import provider_registry

logger = logging.getLogger(__name__)


async def get_sync_status(
    db: AsyncSession,
    user_id: uuid.UUID,
) -> list[ExternalSync]:
    """Return all ExternalSync records for the given user."""
    stmt = select(ExternalSync).where(ExternalSync.user_id == user_id)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def trigger_sync(
    db: AsyncSession,
    user_id: uuid.UUID,
    provider: str,
) -> ExternalSync:
    """Trigger a sync for the given provider and user.

    Raises HTTP 404 if no ExternalSync record exists.
    Raises HTTP 501 if the provider is not registered.
    On provider error, sets status to 'error' and commits.
    """
    stmt = select(ExternalSync).where(
        ExternalSync.user_id == user_id,
        ExternalSync.provider == provider,
    )
    result = await db.execute(stmt)
    sync_record = result.scalar_one_or_none()

    if sync_record is None:
        raise HTTPException(status_code=404, detail="Sync connection not found")

    provider_cls = provider_registry.get(provider)
    if provider_cls is None:
        raise HTTPException(status_code=501, detail="Provider not implemented")

    try:
        provider_instance = provider_cls()
        await provider_instance.sync(db, sync_record)
        sync_record.last_synced_at = datetime.now(UTC)
        sync_record.status = SyncStatus.ACTIVE  # always reset to ACTIVE on success
    except HTTPException:
        raise
    except Exception:
        logger.exception("sync failed for provider %s (user %s)", provider, user_id)
        # last_synced_at is intentionally left unchanged on failure to preserve
        # the last known-good sync timestamp for display purposes.
        sync_record.status = SyncStatus.ERROR

    await db.commit()
    try:
        await db.refresh(sync_record)
    except Exception:
        logger.warning("refresh failed after sync commit for provider %s", provider)
    return sync_record
