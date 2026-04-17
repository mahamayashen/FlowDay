from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any
from urllib.parse import urlencode

import httpx
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import decrypt_oauth_token, encrypt_oauth_token
from app.models.external_sync import ExternalSync

GOOGLE_CALENDAR_SCOPE = "https://www.googleapis.com/auth/calendar.readonly"
GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_CALENDAR_EVENTS_URL = (
    "https://www.googleapis.com/calendar/v3/calendars/primary/events"
)


def build_authorization_url(user_id: str) -> str:
    """Build the Google OAuth consent URL for calendar access."""
    params = {
        "client_id": settings.GOOGLE_CLIENT_ID or "",
        "redirect_uri": settings.GOOGLE_CALENDAR_REDIRECT_URI,
        "response_type": "code",
        "scope": GOOGLE_CALENDAR_SCOPE,
        "access_type": "offline",
        "prompt": "consent",
        "state": user_id,
    }
    return f"{GOOGLE_AUTH_URL}?{urlencode(params)}"


async def _post_to_token_endpoint(payload: dict[str, str]) -> dict[str, Any]:
    """POST form data to the Google token endpoint and return the JSON response."""
    async with httpx.AsyncClient() as client:
        resp = await client.post(GOOGLE_TOKEN_URL, data=payload)
    if resp.status_code != 200:
        raise HTTPException(status_code=401, detail="Google token endpoint request failed")
    return resp.json()


async def exchange_code_for_tokens(code: str) -> dict[str, Any]:
    """Exchange an authorization code for access and refresh tokens."""
    token_data = await _post_to_token_endpoint(
        {
            "code": code,
            "client_id": settings.GOOGLE_CLIENT_ID or "",
            "client_secret": settings.GOOGLE_CLIENT_SECRET or "",
            "redirect_uri": settings.GOOGLE_CALENDAR_REDIRECT_URI,
            "grant_type": "authorization_code",
        }
    )
    if "access_token" not in token_data:
        raise HTTPException(status_code=401, detail="Failed to exchange Google auth code")
    return token_data


async def refresh_access_token(encrypted_refresh_token: str) -> dict[str, Any]:
    """Use a stored refresh token to get a new access token from Google."""
    refresh_token = decrypt_oauth_token(encrypted_refresh_token)
    token_data = await _post_to_token_endpoint(
        {
            "client_id": settings.GOOGLE_CLIENT_ID or "",
            "client_secret": settings.GOOGLE_CLIENT_SECRET or "",
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
        }
    )
    if "access_token" not in token_data:
        raise HTTPException(status_code=401, detail="Failed to refresh Google token")
    return token_data


async def store_tokens_in_sync_record(
    db: AsyncSession,
    sync_record: ExternalSync,
    token_data: dict[str, Any],
) -> None:
    """Encrypt and persist access/refresh tokens in sync_config_json."""
    expires_in: int = token_data.get("expires_in", 3600)
    expiry = (datetime.now(UTC) + timedelta(seconds=expires_in)).isoformat()

    current_config: dict[str, Any] = dict(sync_record.sync_config_json or {})
    current_config["encrypted_access_token"] = encrypt_oauth_token(
        token_data["access_token"]
    )
    if "refresh_token" in token_data:
        current_config["encrypted_refresh_token"] = encrypt_oauth_token(
            token_data["refresh_token"]
        )
    current_config["token_expiry"] = expiry

    sync_record.sync_config_json = current_config
    await db.commit()
    await db.refresh(sync_record)


async def fetch_calendar_events(
    access_token: str,
    time_min: str,
    time_max: str,
) -> list[dict[str, Any]]:
    """Fetch all calendar events in [time_min, time_max] from the primary calendar."""
    headers = {"Authorization": f"Bearer {access_token}"}
    params: dict[str, Any] = {
        "timeMin": time_min,
        "timeMax": time_max,
        "singleEvents": "true",
        "orderBy": "startTime",
    }
    events: list[dict[str, Any]] = []
    async with httpx.AsyncClient() as client:
        while True:
            resp = await client.get(
                GOOGLE_CALENDAR_EVENTS_URL, headers=headers, params=params
            )
            if resp.status_code != 200:
                raise HTTPException(
                    status_code=502, detail="Failed to fetch Google Calendar events"
                )
            data = resp.json()
            events.extend(data.get("items", []))
            next_page = data.get("nextPageToken")
            if not next_page:
                break
            params["pageToken"] = next_page
    return events


async def get_valid_access_token(
    db: AsyncSession,
    sync_record: ExternalSync,
) -> str:
    """Return a valid access token, refreshing from Google if expired."""
    config: dict[str, Any] = sync_record.sync_config_json or {}
    expiry_str: str | None = config.get("token_expiry")
    encrypted_access: str | None = config.get("encrypted_access_token")
    encrypted_refresh: str | None = config.get("encrypted_refresh_token")

    if not encrypted_access or not encrypted_refresh:
        raise HTTPException(
            status_code=401,
            detail="Google Calendar not connected — please re-authorize",
        )

    # Return cached token if still valid (with 60 s buffer)
    if expiry_str:
        expiry = datetime.fromisoformat(expiry_str)
        if datetime.now(UTC) < expiry - timedelta(seconds=60):
            return decrypt_oauth_token(encrypted_access)

    # Token expired — refresh it
    token_data = await refresh_access_token(encrypted_refresh)
    await store_tokens_in_sync_record(db, sync_record, token_data)
    return token_data["access_token"]


async def get_or_create_google_calendar_sync(
    db: AsyncSession,
    user_id: uuid.UUID,
) -> ExternalSync:
    """Upsert an ExternalSync record for google_calendar for the given user."""
    from sqlalchemy import select

    result = await db.execute(
        select(ExternalSync).where(
            ExternalSync.user_id == user_id,
            ExternalSync.provider == "google_calendar",
        )
    )
    record = result.scalar_one_or_none()
    if record is None:
        record = ExternalSync(
            user_id=user_id,
            provider="google_calendar",
            status="active",
            sync_config_json={},
        )
        db.add(record)
        await db.flush()
    return record
