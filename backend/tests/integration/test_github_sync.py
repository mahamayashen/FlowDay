from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decrypt_oauth_token, encrypt_oauth_token
from app.models.external_sync import ExternalSync
from app.models.task import Task
from app.models.user import User
from app.services.github_sync import _sign_github_state


@pytest.mark.asyncio
async def test_github_callback_creates_external_sync_record(
    auth_client: AsyncClient,
    db_session: AsyncSession,
    test_user: User,
) -> None:
    """GET /sync/github/callback creates an ExternalSync row with encrypted token."""
    fake_tokens = {
        "access_token": "ghu_integration_access",
        "token_type": "bearer",
    }

    with patch(
        "app.api.sync.exchange_github_code_for_tokens",
        new_callable=AsyncMock,
        return_value=fake_tokens,
    ):
        resp = await auth_client.get(
            "/sync/github/callback",
            params={
                "code": "auth-code",
                "state": _sign_github_state(str(test_user.id)),
            },
        )

    assert resp.status_code == 200
    data = resp.json()
    assert data["provider"] == "github"
    assert data["status"] == "active"

    # Verify DB row exists with encrypted token
    result = await db_session.execute(
        select(ExternalSync).where(
            ExternalSync.user_id == test_user.id,
            ExternalSync.provider == "github",
        )
    )
    record = result.scalar_one_or_none()
    assert record is not None
    config = record.sync_config_json
    assert "encrypted_access_token" in config
    decrypted = decrypt_oauth_token(config["encrypted_access_token"])
    assert decrypted == "ghu_integration_access"
    # No token_expiry for classic OAuth token
    assert "token_expiry" not in config


@pytest.mark.asyncio
async def test_github_sync_trigger_creates_tasks(
    auth_client: AsyncClient,
    db_session: AsyncSession,
    test_user: User,
) -> None:
    """POST /sync/github/trigger creates Task rows under the GitHub sentinel project."""
    # Pre-insert ExternalSync record with valid token
    sync_record = ExternalSync(
        user_id=test_user.id,
        provider="github",
        status="active",
        sync_config_json={
            "encrypted_access_token": encrypt_oauth_token("ghu_test_token"),
        },
    )
    db_session.add(sync_record)
    await db_session.flush()

    fake_repos = [
        {
            "full_name": "testuser/myrepo",
            "owner": {"login": "testuser"},
            "name": "myrepo",
        },
    ]
    fake_commits = [
        {
            "sha": "def4567890abcdef",
            "commit": {
                "message": "feat: integration test commit",
                "author": {"name": "Test User", "date": "2026-04-18T10:00:00Z"},
            },
        }
    ]

    with (
        patch(
            "app.services.github_sync_provider.fetch_github_repos",
            new_callable=AsyncMock,
            return_value=fake_repos,
        ),
        patch(
            "app.services.github_sync_provider.fetch_github_commits",
            new_callable=AsyncMock,
            return_value=fake_commits,
        ),
        patch(
            "app.services.github_sync_provider.fetch_github_pull_requests",
            new_callable=AsyncMock,
            return_value=[],
        ),
    ):
        resp = await auth_client.post("/sync/github/trigger")

    assert resp.status_code == 200

    # Verify Task rows were created under the GitHub sentinel project
    result = await db_session.execute(select(Task))
    tasks = result.scalars().all()
    github_tasks = [t for t in tasks if t.title and "myrepo" in t.title]
    assert len(github_tasks) >= 1
    assert "def4567" in github_tasks[0].title


@pytest.mark.asyncio
async def test_github_callback_rejected_with_wrong_state(
    auth_client: AsyncClient,
    test_user: User,
) -> None:
    """GET /sync/github/callback with wrong state returns 400."""
    resp = await auth_client.get(
        "/sync/github/callback",
        params={"code": "code", "state": "wrong-user-id"},
    )
    assert resp.status_code == 400
