from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException
from hypothesis import given
from hypothesis import settings as hyp_settings
from hypothesis import strategies as st

from app.core.security import decrypt_oauth_token, encrypt_oauth_token
from app.services.github_sync import (
    GITHUB_AUTH_URL,
    _sign_github_state,
    build_github_authorization_url,
    exchange_github_code_for_tokens,
    fetch_github_commits,
    fetch_github_pull_requests,
    fetch_github_repos,
    get_or_create_github_sync,
    get_valid_github_access_token,
    refresh_github_access_token,
    store_github_tokens_in_sync_record,
    verify_github_state,
)

USER_ID = str(uuid.UUID("00000000-0000-0000-0000-000000000027"))


def _make_httpx_mock(
    method: str = "get", response_data: object = None, status: int = 200
) -> MagicMock:
    """Create a properly configured httpx.AsyncClient mock."""
    mock_resp = MagicMock()
    mock_resp.status_code = status
    mock_resp.json.return_value = response_data or {}

    mock_client = MagicMock()
    coro = AsyncMock(return_value=mock_resp)
    setattr(mock_client, method, coro)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    return mock_client


# ---------------------------------------------------------------------------
# State signing / verification
# ---------------------------------------------------------------------------


def test_sign_github_state_produces_user_dot_signature() -> None:
    """_sign_github_state returns '{user_id}.{hex}' format."""
    result = _sign_github_state(USER_ID)
    parts = result.split(".")
    assert len(parts) == 2
    assert parts[0] == USER_ID
    assert len(parts[1]) == 16


def test_verify_github_state_accepts_valid_state() -> None:
    """verify_github_state returns True for a state produced by _sign_github_state."""
    state = _sign_github_state(USER_ID)
    assert verify_github_state(state, USER_ID) is True


def test_verify_github_state_rejects_tampered_state() -> None:
    """verify_github_state returns False for a tampered or invalid state."""
    assert verify_github_state("wrong-state", USER_ID) is False
    assert verify_github_state(f"{USER_ID}.badsig", USER_ID) is False


# ---------------------------------------------------------------------------
# build_github_authorization_url
# ---------------------------------------------------------------------------


def test_build_github_authorization_url_contains_required_params() -> None:
    """Authorization URL must include client_id, redirect_uri, scope, state."""
    url = build_github_authorization_url(USER_ID)
    assert url.startswith(GITHUB_AUTH_URL)
    assert "scope=repo" in url
    assert USER_ID in url


@hyp_settings(max_examples=20)
@given(st.uuids().map(str))
def test_build_github_authorization_url_state_contains_user_id(
    user_id: str,
) -> None:
    """State parameter in URL contains the user_id as a prefix."""
    url = build_github_authorization_url(user_id)
    assert f"state={user_id}." in url


# ---------------------------------------------------------------------------
# exchange_github_code_for_tokens
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_exchange_github_code_success_returns_tokens() -> None:
    """exchange_github_code_for_tokens returns access token dict."""
    fake_tokens = {"access_token": "ghu_access123", "token_type": "bearer"}
    with patch(
        "app.services.github_sync._post_to_github_token_endpoint",
        new_callable=AsyncMock,
        return_value=fake_tokens,
    ):
        result = await exchange_github_code_for_tokens("auth-code")

    assert result["access_token"] == "ghu_access123"


@pytest.mark.asyncio
async def test_exchange_github_code_failure_raises_401() -> None:
    """exchange_github_code_for_tokens raises 401 when token endpoint fails."""
    with patch(
        "app.services.github_sync._post_to_github_token_endpoint",
        new_callable=AsyncMock,
        side_effect=HTTPException(status_code=401, detail="fail"),
    ):
        with pytest.raises(HTTPException) as exc_info:
            await exchange_github_code_for_tokens("bad-code")

    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_exchange_github_code_raises_when_no_access_token() -> None:
    """exchange_github_code_for_tokens raises 401 when response lacks access_token."""
    with patch(
        "app.services.github_sync._post_to_github_token_endpoint",
        new_callable=AsyncMock,
        return_value={"token_type": "bearer"},
    ):
        with pytest.raises(HTTPException) as exc_info:
            await exchange_github_code_for_tokens("code-no-token")

    assert exc_info.value.status_code == 401


# ---------------------------------------------------------------------------
# refresh_github_access_token
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_refresh_github_access_token_success() -> None:
    """refresh_github_access_token decrypts the refresh token and returns tokens."""
    encrypted = encrypt_oauth_token("my-refresh-token")

    with patch(
        "app.services.github_sync._post_to_github_token_endpoint",
        new_callable=AsyncMock,
        return_value={"access_token": "new-access", "expires_in": 28800},
    ):
        result = await refresh_github_access_token(encrypted)

    assert result["access_token"] == "new-access"


@pytest.mark.asyncio
async def test_refresh_github_access_token_failure_raises_401() -> None:
    """refresh_github_access_token raises 401 when token endpoint fails."""
    encrypted = encrypt_oauth_token("bad-refresh-token")

    with patch(
        "app.services.github_sync._post_to_github_token_endpoint",
        new_callable=AsyncMock,
        side_effect=HTTPException(status_code=401, detail="fail"),
    ):
        with pytest.raises(HTTPException) as exc_info:
            await refresh_github_access_token(encrypted)

    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_refresh_github_access_token_raises_when_no_access_token() -> None:
    """refresh_github_access_token raises 401 when response lacks access_token."""
    encrypted = encrypt_oauth_token("refresh-token")

    with patch(
        "app.services.github_sync._post_to_github_token_endpoint",
        new_callable=AsyncMock,
        return_value={"token_type": "bearer"},
    ):
        with pytest.raises(HTTPException) as exc_info:
            await refresh_github_access_token(encrypted)

    assert exc_info.value.status_code == 401


# ---------------------------------------------------------------------------
# store_github_tokens_in_sync_record
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_store_github_tokens_encrypts_access_token() -> None:
    """store_github_tokens_in_sync_record encrypts the access token."""
    sync_record = MagicMock()
    sync_record.sync_config_json = {}
    db = AsyncMock()

    token_data = {"access_token": "plain-access", "token_type": "bearer"}
    await store_github_tokens_in_sync_record(db, sync_record, token_data)

    stored = sync_record.sync_config_json
    assert "encrypted_access_token" in stored
    assert stored["encrypted_access_token"] != "plain-access"
    assert decrypt_oauth_token(stored["encrypted_access_token"]) == "plain-access"


@pytest.mark.asyncio
async def test_store_github_tokens_encrypts_refresh_token_when_present() -> None:
    """store_github_tokens_in_sync_record encrypts refresh token if provided."""
    sync_record = MagicMock()
    sync_record.sync_config_json = {}
    db = AsyncMock()

    token_data = {
        "access_token": "access",
        "refresh_token": "refresh",
        "expires_in": 28800,
    }
    await store_github_tokens_in_sync_record(db, sync_record, token_data)

    stored = sync_record.sync_config_json
    assert decrypt_oauth_token(stored["encrypted_refresh_token"]) == "refresh"
    assert "token_expiry" in stored


@pytest.mark.asyncio
async def test_store_github_tokens_omits_expiry_when_no_expires_in() -> None:
    """store_github_tokens omits token_expiry for classic OAuth tokens (no expiry)."""
    sync_record = MagicMock()
    sync_record.sync_config_json = {}
    db = AsyncMock()

    token_data = {"access_token": "classic-token", "token_type": "bearer"}
    await store_github_tokens_in_sync_record(db, sync_record, token_data)

    stored = sync_record.sync_config_json
    assert "token_expiry" not in stored


# ---------------------------------------------------------------------------
# get_valid_github_access_token
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_valid_github_token_returns_stored_without_expiry() -> None:
    """get_valid_github_access_token returns token when no token_expiry (classic)."""
    sync_record = MagicMock()
    sync_record.sync_config_json = {
        "encrypted_access_token": encrypt_oauth_token("classic-token"),
    }
    db = AsyncMock()

    result = await get_valid_github_access_token(db, sync_record)
    assert result == "classic-token"


@pytest.mark.asyncio
async def test_get_valid_github_token_returns_cached_when_not_expired() -> None:
    """get_valid_github_access_token returns cached token without refreshing."""
    future = (datetime.now(UTC) + timedelta(hours=8)).isoformat()
    sync_record = MagicMock()
    sync_record.sync_config_json = {
        "encrypted_access_token": encrypt_oauth_token("cached-token"),
        "encrypted_refresh_token": encrypt_oauth_token("refresh-token"),
        "token_expiry": future,
    }
    db = AsyncMock()

    with patch(
        "app.services.github_sync.refresh_github_access_token",
        new_callable=AsyncMock,
    ) as mock_refresh:
        result = await get_valid_github_access_token(db, sync_record)

    assert result == "cached-token"
    mock_refresh.assert_not_called()


@pytest.mark.asyncio
async def test_get_valid_github_token_refreshes_when_expired() -> None:
    """get_valid_github_access_token refreshes when expiry has passed."""
    past = (datetime.now(UTC) - timedelta(hours=1)).isoformat()
    sync_record = MagicMock()
    sync_record.sync_config_json = {
        "encrypted_access_token": encrypt_oauth_token("old-token"),
        "encrypted_refresh_token": encrypt_oauth_token("refresh-token"),
        "token_expiry": past,
    }
    db = AsyncMock()

    new_token_data = {"access_token": "fresh-token", "expires_in": 28800}

    with (
        patch(
            "app.services.github_sync.refresh_github_access_token",
            new_callable=AsyncMock,
            return_value=new_token_data,
        ),
        patch(
            "app.services.github_sync.store_github_tokens_in_sync_record",
            new_callable=AsyncMock,
        ),
    ):
        result = await get_valid_github_access_token(db, sync_record)

    assert result == "fresh-token"


@pytest.mark.asyncio
async def test_get_valid_github_token_raises_when_no_tokens() -> None:
    """get_valid_github_access_token raises 401 when no tokens stored."""
    sync_record = MagicMock()
    sync_record.sync_config_json = {}
    db = AsyncMock()

    with pytest.raises(HTTPException) as exc_info:
        await get_valid_github_access_token(db, sync_record)

    assert exc_info.value.status_code == 401


# ---------------------------------------------------------------------------
# get_or_create_github_sync
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_or_create_github_sync_creates_new_record() -> None:
    """get_or_create_github_sync creates a new ExternalSync when none exists."""
    db = AsyncMock()
    result_mock = MagicMock()
    result_mock.scalar_one_or_none.return_value = None
    db.execute = AsyncMock(return_value=result_mock)

    user_id = uuid.uuid4()
    record = await get_or_create_github_sync(db, user_id)

    assert record.provider == "github"
    assert record.user_id == user_id
    db.add.assert_called_once()
    db.flush.assert_called_once()


@pytest.mark.asyncio
async def test_get_or_create_github_sync_returns_existing() -> None:
    """get_or_create_github_sync returns existing record without creating a new one."""
    from app.models.external_sync import ExternalSync

    user_id = uuid.uuid4()
    existing = MagicMock(spec=ExternalSync)
    existing.provider = "github"
    existing.user_id = user_id

    db = AsyncMock()
    result_mock = MagicMock()
    result_mock.scalar_one_or_none.return_value = existing
    db.execute = AsyncMock(return_value=result_mock)

    record = await get_or_create_github_sync(db, user_id)

    assert record is existing
    db.add.assert_not_called()


# ---------------------------------------------------------------------------
# fetch_github_repos
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_fetch_github_repos_returns_list() -> None:
    """fetch_github_repos returns a list of repo dicts."""
    repos = [
        {
            "id": 1,
            "full_name": "user/repo1",
            "owner": {"login": "user"},
            "name": "repo1",
        },  # noqa: E501
        {
            "id": 2,
            "full_name": "user/repo2",
            "owner": {"login": "user"},
            "name": "repo2",
        },  # noqa: E501
    ]
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = repos

    # Second page empty to stop pagination
    mock_resp2 = MagicMock()
    mock_resp2.status_code = 200
    mock_resp2.json.return_value = []

    mock_client = MagicMock()
    mock_client.get = AsyncMock(side_effect=[mock_resp, mock_resp2])
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with patch("app.services.github_sync.httpx.AsyncClient", return_value=mock_client):
        result = await fetch_github_repos("access-token")

    assert len(result) == 2
    assert result[0]["full_name"] == "user/repo1"


@pytest.mark.asyncio
async def test_fetch_github_repos_raises_on_error() -> None:
    """fetch_github_repos raises HTTPException 502 on GitHub API error."""
    mock_client = _make_httpx_mock("get", {"message": "Unauthorized"}, 401)

    with patch("app.services.github_sync.httpx.AsyncClient", return_value=mock_client):
        with pytest.raises(HTTPException) as exc_info:
            await fetch_github_repos("bad-token")

    assert exc_info.value.status_code == 502


# ---------------------------------------------------------------------------
# fetch_github_commits
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_fetch_github_commits_returns_commits_for_date_range() -> None:
    """fetch_github_commits returns a list of commit dicts."""
    commits = [
        {
            "sha": "abc123",
            "commit": {
                "message": "fix: thing",
                "author": {"date": "2026-04-18T10:00:00Z"},
            },
        },
    ]
    mock_client = _make_httpx_mock("get", commits, 200)

    with patch("app.services.github_sync.httpx.AsyncClient", return_value=mock_client):
        result = await fetch_github_commits(
            "access-token",
            "user",
            "repo1",
            "2026-04-11T00:00:00Z",
            "2026-04-18T23:59:59Z",
        )

    assert len(result) == 1
    assert result[0]["sha"] == "abc123"


# ---------------------------------------------------------------------------
# fetch_github_pull_requests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_fetch_github_pull_requests_returns_prs() -> None:
    """fetch_github_pull_requests returns a list of PR dicts."""
    prs = [
        {"number": 42, "title": "Add feature", "state": "open"},
    ]
    mock_client = _make_httpx_mock("get", prs, 200)

    with patch("app.services.github_sync.httpx.AsyncClient", return_value=mock_client):
        result = await fetch_github_pull_requests("access-token", "user", "repo1")

    assert len(result) == 1
    assert result[0]["number"] == 42
