from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.external_sync import SyncProvider
from app.models.user import User
from app.schemas.sync import GoogleCalendarAuthResponse, SyncStatusResponse
from app.services.google_calendar import (
    build_authorization_url,
    exchange_code_for_tokens,
    get_or_create_google_calendar_sync,
    store_tokens_in_sync_record,
    verify_state,
)
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
    provider: SyncProvider,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SyncStatusResponse:
    """Manually trigger a sync for the given provider."""
    record = await trigger_sync(db=db, user_id=current_user.id, provider=provider)
    return SyncStatusResponse.model_validate(record)


@router.get("/google-calendar/auth", response_model=GoogleCalendarAuthResponse)
async def google_calendar_auth_route(
    current_user: User = Depends(get_current_user),
) -> GoogleCalendarAuthResponse:
    """Initiate Google Calendar OAuth consent flow."""
    url = build_authorization_url(str(current_user.id))
    return GoogleCalendarAuthResponse(authorization_url=url)


@router.get("/google-calendar/callback", response_model=SyncStatusResponse)
async def google_calendar_callback_route(
    code: str,
    state: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SyncStatusResponse:
    """Handle Google Calendar OAuth callback, store tokens, and return sync record."""
    if not verify_state(state, str(current_user.id)):
        raise HTTPException(status_code=400, detail="Invalid OAuth state parameter")

    token_data = await exchange_code_for_tokens(code)
    sync_record = await get_or_create_google_calendar_sync(db, current_user.id)
    await store_tokens_in_sync_record(db, sync_record, token_data)
    return SyncStatusResponse.model_validate(sync_record)
