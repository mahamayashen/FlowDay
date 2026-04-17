from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException
from hypothesis import given
from hypothesis import settings as hyp_settings
from hypothesis import strategies as st

from app.core.security import encrypt_oauth_token
from app.services.google_calendar import (
    GOOGLE_AUTH_URL,
    build_authorization_url,
    exchange_code_for_tokens,
    fetch_calendar_events,
    get_valid_access_token,
    refresh_access_token,
    store_tokens_in_sync_record,
)

USER_ID = str(uuid.UUID("00000000-0000-0000-0000-000000000003"))


# ---------------------------------------------------------------------------
# build_authorization_url
# ---------------------------------------------------------------------------


def test_build_authorization_url_contains_required_params() -> None:
    """Authorization URL must include scope, access_type=offline, state."""
    url = build_authorization_url(USER_ID)
    assert url.startswith(GOOGLE_AUTH_URL)
    assert "calendar.readonly" in url
    assert "access_type=offline" in url
    assert "prompt=consent" in url
    assert USER_ID in url


@hyp_settings(max_examples=20)
@given(st.uuids().map(str))
def test_build_authorization_url_state_matches_user_id(user_id: str) -> None:
    """State parameter in URL always equals the provided user_id."""
    url = build_authorization_url(user_id)
    assert f"state={user_id}" in url


# ---------------------------------------------------------------------------
# exchange_code_for_tokens
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_exchange_code_success_returns_tokens() -> None:
    """exchange_code_for_tokens returns access and refresh tokens on success."""
    fake_tokens = {
        "access_token": "access-abc",
        "refresh_token": "refresh-xyz",
        "expires_in": 3600,
    }
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = fake_tokens

    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=mock_resp)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with patch(
        "app.services.google_calendar.httpx.AsyncClient", return_value=mock_client
    ):
        result = await exchange_code_for_tokens("auth-code")

    assert result["access_token"] == "access-abc"
    assert result["refresh_token"] == "refresh-xyz"


@pytest.mark.asyncio
async def test_exchange_code_failure_raises_http_exception() -> None:
    """exchange_code_for_tokens raises HTTPException 401 when Google returns error."""
    mock_resp = MagicMock()
    mock_resp.status_code = 400
    mock_resp.json.return_value = {"error": "invalid_grant"}

    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=mock_resp)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with patch(
        "app.services.google_calendar.httpx.AsyncClient", return_value=mock_client
    ):
        with pytest.raises(HTTPException) as exc_info:
            await exchange_code_for_tokens("bad-code")

    assert exc_info.value.status_code == 401


# ---------------------------------------------------------------------------
# refresh_access_token
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_refresh_access_token_success() -> None:
    """refresh_access_token decrypts the refresh token and posts to Google."""
    encrypted = encrypt_oauth_token("my-refresh-token")

    fake_response = {"access_token": "new-access", "expires_in": 3600}
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = fake_response

    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=mock_resp)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with patch(
        "app.services.google_calendar.httpx.AsyncClient", return_value=mock_client
    ):
        result = await refresh_access_token(encrypted)

    assert result["access_token"] == "new-access"


@pytest.mark.asyncio
async def test_refresh_failure_raises_http_exception() -> None:
    """refresh_access_token raises HTTPException 401 when Google returns error."""
    encrypted = encrypt_oauth_token("bad-refresh-token")

    mock_resp = MagicMock()
    mock_resp.status_code = 400
    mock_resp.json.return_value = {"error": "invalid_grant"}

    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=mock_resp)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with patch(
        "app.services.google_calendar.httpx.AsyncClient", return_value=mock_client
    ):
        with pytest.raises(HTTPException) as exc_info:
            await refresh_access_token(encrypted)

    assert exc_info.value.status_code == 401


# ---------------------------------------------------------------------------
# fetch_calendar_events
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_fetch_calendar_events_returns_list() -> None:
    """fetch_calendar_events returns a list of event dicts."""
    events = [{"id": "evt1", "summary": "Meeting"}]
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"items": events}

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_resp)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with patch(
        "app.services.google_calendar.httpx.AsyncClient", return_value=mock_client
    ):
        result = await fetch_calendar_events(
            "token", "2026-01-01T00:00:00Z", "2026-01-08T00:00:00Z"
        )

    assert len(result) == 1
    assert result[0]["summary"] == "Meeting"


@pytest.mark.asyncio
async def test_fetch_calendar_events_handles_pagination() -> None:
    """fetch_calendar_events follows nextPageToken to collect all events."""
    page1 = {"items": [{"id": "e1"}], "nextPageToken": "tok123"}
    page2 = {"items": [{"id": "e2"}]}

    mock_resp1 = MagicMock()
    mock_resp1.status_code = 200
    mock_resp1.json.return_value = page1

    mock_resp2 = MagicMock()
    mock_resp2.status_code = 200
    mock_resp2.json.return_value = page2

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(side_effect=[mock_resp1, mock_resp2])
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with patch(
        "app.services.google_calendar.httpx.AsyncClient", return_value=mock_client
    ):
        result = await fetch_calendar_events(
            "token", "2026-01-01T00:00:00Z", "2026-01-08T00:00:00Z"
        )

    assert len(result) == 2
    assert result[0]["id"] == "e1"
    assert result[1]["id"] == "e2"


@pytest.mark.asyncio
async def test_fetch_calendar_events_raises_on_error() -> None:
    """fetch_calendar_events raises HTTPException 502 when Google returns error."""
    mock_resp = MagicMock()
    mock_resp.status_code = 403
    mock_resp.json.return_value = {"error": "forbidden"}

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_resp)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with patch(
        "app.services.google_calendar.httpx.AsyncClient", return_value=mock_client
    ):
        with pytest.raises(HTTPException) as exc_info:
            await fetch_calendar_events(
                "token", "2026-01-01T00:00:00Z", "2026-01-08T00:00:00Z"
            )

    assert exc_info.value.status_code == 502


# ---------------------------------------------------------------------------
# store_tokens_in_sync_record
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_store_tokens_encrypts_access_and_refresh() -> None:
    """store_tokens_in_sync_record encrypts tokens before storing."""
    from app.core.security import decrypt_oauth_token

    sync_record = MagicMock()
    sync_record.sync_config_json = {}
    db = AsyncMock()

    token_data = {
        "access_token": "plain-access",
        "refresh_token": "plain-refresh",
        "expires_in": 3600,
    }
    await store_tokens_in_sync_record(db, sync_record, token_data)

    stored = sync_record.sync_config_json
    assert stored["encrypted_access_token"] != "plain-access"
    assert stored["encrypted_refresh_token"] != "plain-refresh"
    assert decrypt_oauth_token(stored["encrypted_access_token"]) == "plain-access"
    assert decrypt_oauth_token(stored["encrypted_refresh_token"]) == "plain-refresh"
    assert "token_expiry" in stored


@pytest.mark.asyncio
async def test_store_tokens_preserves_existing_refresh_when_omitted() -> None:
    """store_tokens_in_sync_record keeps old refresh token when token_data omits it."""
    old_encrypted_refresh = encrypt_oauth_token("old-refresh")
    sync_record = MagicMock()
    sync_record.sync_config_json = {"encrypted_refresh_token": old_encrypted_refresh}
    db = AsyncMock()

    token_data = {"access_token": "new-access", "expires_in": 3600}
    await store_tokens_in_sync_record(db, sync_record, token_data)

    assert (
        sync_record.sync_config_json["encrypted_refresh_token"] == old_encrypted_refresh
    )


# ---------------------------------------------------------------------------
# get_valid_access_token
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_valid_token_returns_cached_when_not_expired() -> None:
    """get_valid_access_token returns cached token without refreshing if still valid."""
    future = (datetime.now(UTC) + timedelta(hours=1)).isoformat()
    sync_record = MagicMock()
    sync_record.sync_config_json = {
        "encrypted_access_token": encrypt_oauth_token("cached-token"),
        "encrypted_refresh_token": encrypt_oauth_token("refresh-token"),
        "token_expiry": future,
    }
    db = AsyncMock()

    with patch(
        "app.services.google_calendar.refresh_access_token", new_callable=AsyncMock
    ) as mock_refresh:
        result = await get_valid_access_token(db, sync_record)

    assert result == "cached-token"
    mock_refresh.assert_not_called()


@pytest.mark.asyncio
async def test_get_valid_token_refreshes_when_expired() -> None:
    """get_valid_access_token refreshes the token when expiry has passed."""
    past = (datetime.now(UTC) - timedelta(hours=1)).isoformat()
    sync_record = MagicMock()
    sync_record.sync_config_json = {
        "encrypted_access_token": encrypt_oauth_token("old-token"),
        "encrypted_refresh_token": encrypt_oauth_token("refresh-token"),
        "token_expiry": past,
    }
    db = AsyncMock()

    new_token_data = {"access_token": "fresh-token", "expires_in": 3600}

    with (
        patch(
            "app.services.google_calendar.refresh_access_token",
            new_callable=AsyncMock,
            return_value=new_token_data,
        ),
        patch(
            "app.services.google_calendar.store_tokens_in_sync_record",
            new_callable=AsyncMock,
        ),
    ):
        result = await get_valid_access_token(db, sync_record)

    assert result == "fresh-token"


@pytest.mark.asyncio
async def test_get_valid_token_raises_when_no_tokens() -> None:
    """get_valid_access_token raises 401 HTTPException when no tokens stored."""
    sync_record = MagicMock()
    sync_record.sync_config_json = {}
    db = AsyncMock()

    with pytest.raises(HTTPException) as exc_info:
        await get_valid_access_token(db, sync_record)

    assert exc_info.value.status_code == 401
