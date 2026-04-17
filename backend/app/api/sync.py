from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.sync import SyncStatusResponse
from app.services.sync_service import get_sync_status, trigger_sync

router = APIRouter(prefix="/sync", tags=["sync"])


@router.get("/status", response_model=list[SyncStatusResponse])
async def get_sync_status_route(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[SyncStatusResponse]:
    """Return all sync connections for the current user."""
    records = await get_sync_status(db=db, user_id=current_user.id)
    return [SyncStatusResponse.model_validate(r) for r in records]


@router.post("/{provider}/trigger", response_model=SyncStatusResponse)
async def trigger_sync_route(
    provider: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SyncStatusResponse:
    """Manually trigger a sync for the given provider."""
    record = await trigger_sync(db=db, user_id=current_user.id, provider=provider)
    return SyncStatusResponse.model_validate(record)
