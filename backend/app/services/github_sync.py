from __future__ import annotations

import hashlib
import hmac
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any, cast
from urllib.parse import urlencode

import httpx
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import decrypt_oauth_token, encrypt_oauth_token
from app.models.external_sync import ExternalSync

GITHUB_AUTH_URL = "https://github.com/login/oauth/authorize"
GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"
GITHUB_API_BASE = "https://api.github.com"
GITHUB_SYNC_SCOPE = "repo"


def _sign_github_state(user_id: str) -> str:
    """Create an HMAC-signed state parameter: user_id.signature."""
    sig = hmac.new(
        settings.SECRET_KEY.encode(), user_id.encode(), hashlib.sha256
    ).hexdigest()[:16]
    return f"{user_id}.{sig}"


def verify_github_state(state: str, user_id: str) -> bool:
    """Verify that state was signed by this server for this user."""
    return hmac.compare_digest(state, _sign_github_state(user_id))


def build_github_authorization_url(user_id: str) -> str:
    """Build the GitHub OAuth consent URL for sync access."""
    params = {
        "client_id": settings.GITHUB_CLIENT_ID or "",
        "redirect_uri": settings.GITHUB_SYNC_REDIRECT_URI,
        "scope": GITHUB_SYNC_SCOPE,
        "state": _sign_github_state(user_id),
    }
    return f"{GITHUB_AUTH_URL}?{urlencode(params)}"


async def _post_to_github_token_endpoint(payload: dict[str, str]) -> dict[str, Any]:
    """POST to the GitHub token endpoint and return the JSON response."""
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            GITHUB_TOKEN_URL,
            data=payload,
            headers={"Accept": "application/json"},
        )
    if resp.status_code != 200:
        raise HTTPException(
            status_code=401, detail="GitHub token endpoint request failed"
        )
    return cast(dict[str, Any], resp.json())


async def exchange_github_code_for_tokens(code: str) -> dict[str, Any]:
    """Exchange an authorization code for a GitHub access token."""
    token_data = await _post_to_github_token_endpoint(
        {
            "code": code,
            "client_id": settings.GITHUB_CLIENT_ID or "",
            "client_secret": settings.GITHUB_CLIENT_SECRET or "",
            "redirect_uri": settings.GITHUB_SYNC_REDIRECT_URI,
        }
    )
    if "access_token" not in token_data:
        raise HTTPException(
            status_code=401, detail="Failed to exchange GitHub auth code"
        )
    return token_data


async def refresh_github_access_token(
    encrypted_refresh_token: str,
) -> dict[str, Any]:
    """Use a stored refresh token to get a new access token from GitHub."""
    refresh_token = decrypt_oauth_token(encrypted_refresh_token)
    token_data = await _post_to_github_token_endpoint(
        {
            "client_id": settings.GITHUB_CLIENT_ID or "",
            "client_secret": settings.GITHUB_CLIENT_SECRET or "",
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
        }
    )
    if "access_token" not in token_data:
        raise HTTPException(status_code=401, detail="Failed to refresh GitHub token")
    return token_data


async def store_github_tokens_in_sync_record(
    db: AsyncSession,
    sync_record: ExternalSync,
    token_data: dict[str, Any],
) -> None:
    """Encrypt and persist GitHub tokens in sync_config_json.

    GitHub classic OAuth tokens have no expiry, so token_expiry is only
    stored when expires_in is present in the token response (GitHub Apps).
    """
    current_config: dict[str, Any] = dict(sync_record.sync_config_json or {})
    current_config["encrypted_access_token"] = encrypt_oauth_token(
        token_data["access_token"]
    )
    if "refresh_token" in token_data:
        current_config["encrypted_refresh_token"] = encrypt_oauth_token(
            token_data["refresh_token"]
        )
    if "expires_in" in token_data:
        expires_in = int(token_data["expires_in"])
        expiry = (datetime.now(UTC) + timedelta(seconds=expires_in)).isoformat()
        current_config["token_expiry"] = expiry

    sync_record.sync_config_json = current_config
    await db.commit()
    await db.refresh(sync_record)


async def get_valid_github_access_token(
    db: AsyncSession,
    sync_record: ExternalSync,
) -> str:
    """Return a valid GitHub access token, refreshing if expired.

    Classic GitHub OAuth tokens never expire, so if no token_expiry is stored
    the cached access token is returned directly without checking expiry.
    """
    config: dict[str, Any] = sync_record.sync_config_json or {}
    encrypted_access: str | None = config.get("encrypted_access_token")
    encrypted_refresh: str | None = config.get("encrypted_refresh_token")
    expiry_str: str | None = config.get("token_expiry")

    if not encrypted_access:
        raise HTTPException(
            status_code=401,
            detail="GitHub not connected — please re-authorize",
        )

    # Classic token: no expiry recorded — return as-is
    if not expiry_str:
        return decrypt_oauth_token(encrypted_access)

    # Token with expiry: return cached if still valid (60 s buffer)
    expiry = datetime.fromisoformat(expiry_str)
    if datetime.now(UTC) < expiry - timedelta(seconds=60):
        return decrypt_oauth_token(encrypted_access)

    # Token expired — refresh it (requires a stored refresh token)
    if not encrypted_refresh:
        raise HTTPException(
            status_code=401,
            detail="GitHub token expired and no refresh token available",
        )
    token_data = await refresh_github_access_token(encrypted_refresh)
    await store_github_tokens_in_sync_record(db, sync_record, token_data)
    return str(token_data["access_token"])


async def get_or_create_github_sync(
    db: AsyncSession,
    user_id: uuid.UUID,
) -> ExternalSync:
    """Upsert an ExternalSync record for github for the given user."""
    from sqlalchemy import select

    result = await db.execute(
        select(ExternalSync).where(
            ExternalSync.user_id == user_id,
            ExternalSync.provider == "github",
        )
    )
    record = result.scalar_one_or_none()
    if record is None:
        record = ExternalSync(
            user_id=user_id,
            provider="github",
            status="active",
            sync_config_json={},
        )
        db.add(record)
        await db.flush()
    return record


async def fetch_github_repos(access_token: str) -> list[dict[str, Any]]:
    """Fetch all repos accessible by the authenticated user (paginated)."""
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/vnd.github+json",
    }
    repos: list[dict[str, Any]] = []
    page = 1
    async with httpx.AsyncClient() as client:
        while True:
            resp = await client.get(
                f"{GITHUB_API_BASE}/user/repos",
                headers=headers,
                params={"per_page": 100, "page": page},
            )
            if resp.status_code != 200:
                raise HTTPException(
                    status_code=502, detail="Failed to fetch GitHub repositories"
                )
            page_data = cast(list[dict[str, Any]], resp.json())
            if not page_data:
                break
            repos.extend(page_data)
            page += 1
    return repos


async def fetch_github_commits(
    access_token: str,
    owner: str,
    repo: str,
    since: str,
    until: str,
) -> list[dict[str, Any]]:
    """Fetch commits for a repo within a date range."""
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/vnd.github+json",
    }
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{GITHUB_API_BASE}/repos/{owner}/{repo}/commits",
            headers=headers,
            params={"since": since, "until": until, "per_page": 100},
        )
    if resp.status_code != 200:
        return []
    return cast(list[dict[str, Any]], resp.json())


async def fetch_github_pull_requests(
    access_token: str,
    owner: str,
    repo: str,
    state: str = "all",
) -> list[dict[str, Any]]:
    """Fetch pull requests for a repo."""
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/vnd.github+json",
    }
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{GITHUB_API_BASE}/repos/{owner}/{repo}/pulls",
            headers=headers,
            params={"state": state, "per_page": 100},
        )
    if resp.status_code != 200:
        return []
    return cast(list[dict[str, Any]], resp.json())
