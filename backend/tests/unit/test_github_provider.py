from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.security import encrypt_oauth_token
from app.services.sync_provider import provider_registry

# ---------------------------------------------------------------------------
# Provider registration
# ---------------------------------------------------------------------------


def test_github_sync_provider_registered_in_registry() -> None:
    """GitHubSyncProvider must be registered under 'github'."""
    import app.services.github_sync_provider  # noqa: F401
    from app.services.github_sync_provider import GitHubSyncProvider

    registered = provider_registry.get("github")
    assert registered is GitHubSyncProvider


def test_github_sync_provider_is_subclass_of_base() -> None:
    """GitHubSyncProvider is a BaseSyncProvider."""
    import app.services.github_sync_provider  # noqa: F401
    from app.services.github_sync_provider import GitHubSyncProvider
    from app.services.sync_provider import BaseSyncProvider

    assert issubclass(GitHubSyncProvider, BaseSyncProvider)


# ---------------------------------------------------------------------------
# sync() — sentinel project and task creation
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_sync_creates_sentinel_project_and_tasks() -> None:
    """sync() creates a sentinel 'GitHub' project and Task rows for commits."""
    import app.services.github_sync_provider  # noqa: F401
    from app.services.github_sync_provider import GitHubSyncProvider

    provider = GitHubSyncProvider()

    sync_record = MagicMock()
    sync_record.user_id = uuid.uuid4()
    sync_record.sync_config_json = {
        "encrypted_access_token": encrypt_oauth_token("tok"),
        "token_expiry": (datetime.now(UTC) + timedelta(hours=1)).isoformat(),
    }

    fake_repos = [
        {"full_name": "user/repo1", "owner": {"login": "user"}, "name": "repo1"},
    ]
    fake_commits = [
        {
            "sha": "abc1234",
            "commit": {
                "message": "feat: add thing",
                "author": {"name": "Dev", "date": "2026-04-18T10:00:00Z"},
            },
        }
    ]

    db = AsyncMock()
    db.execute = AsyncMock(return_value=_mock_scalar_none())

    with (
        patch(
            "app.services.github_sync_provider.get_valid_github_access_token",
            new_callable=AsyncMock,
            return_value="access-token",
        ),
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
        await provider.sync(db, sync_record)

    # db.add should be called at least once (project + task)
    assert db.add.call_count >= 1
    assert db.flush.called


@pytest.mark.asyncio
async def test_sync_creates_tasks_for_pull_requests() -> None:
    """sync() creates Task rows for pull requests."""
    import app.services.github_sync_provider  # noqa: F401
    from app.models.task import Task
    from app.services.github_sync_provider import GitHubSyncProvider

    provider = GitHubSyncProvider()

    sync_record = MagicMock()
    sync_record.user_id = uuid.uuid4()
    sync_record.sync_config_json = {
        "encrypted_access_token": encrypt_oauth_token("tok"),
    }

    fake_repos = [
        {"full_name": "user/repo1", "owner": {"login": "user"}, "name": "repo1"},
    ]
    fake_prs = [
        {
            "number": 42,
            "title": "Add feature X",
            "state": "open",
            "created_at": "2026-04-15T09:00:00Z",
            "merged_at": None,
        }
    ]

    db = AsyncMock()
    db.execute = AsyncMock(return_value=_mock_scalar_none())

    with (
        patch(
            "app.services.github_sync_provider.get_valid_github_access_token",
            new_callable=AsyncMock,
            return_value="access-token",
        ),
        patch(
            "app.services.github_sync_provider.fetch_github_repos",
            new_callable=AsyncMock,
            return_value=fake_repos,
        ),
        patch(
            "app.services.github_sync_provider.fetch_github_commits",
            new_callable=AsyncMock,
            return_value=[],
        ),
        patch(
            "app.services.github_sync_provider.fetch_github_pull_requests",
            new_callable=AsyncMock,
            return_value=fake_prs,
        ),
    ):
        await provider.sync(db, sync_record)

    added_types = [type(call.args[0]) for call in db.add.call_args_list if call.args]
    assert Task in added_types


@pytest.mark.asyncio
async def test_sync_handles_empty_repos() -> None:
    """sync() creates no tasks when there are no repos."""
    import app.services.github_sync_provider  # noqa: F401
    from app.models.task import Task
    from app.services.github_sync_provider import GitHubSyncProvider

    provider = GitHubSyncProvider()

    sync_record = MagicMock()
    sync_record.user_id = uuid.uuid4()
    sync_record.sync_config_json = {
        "encrypted_access_token": encrypt_oauth_token("tok"),
    }

    db = AsyncMock()
    db.execute = AsyncMock(return_value=_mock_scalar_none())

    with (
        patch(
            "app.services.github_sync_provider.get_valid_github_access_token",
            new_callable=AsyncMock,
            return_value="access-token",
        ),
        patch(
            "app.services.github_sync_provider.fetch_github_repos",
            new_callable=AsyncMock,
            return_value=[],
        ),
    ):
        await provider.sync(db, sync_record)

    added_types = [type(call.args[0]) for call in db.add.call_args_list if call.args]
    assert Task not in added_types


@pytest.mark.asyncio
async def test_sync_token_error_propagates() -> None:
    """sync() propagates HTTPException when token retrieval fails."""
    from fastapi import HTTPException

    import app.services.github_sync_provider  # noqa: F401
    from app.services.github_sync_provider import GitHubSyncProvider

    provider = GitHubSyncProvider()
    sync_record = MagicMock()
    sync_record.user_id = uuid.uuid4()
    sync_record.sync_config_json = {}
    db = AsyncMock()

    with patch(
        "app.services.github_sync_provider.get_valid_github_access_token",
        new_callable=AsyncMock,
        side_effect=HTTPException(status_code=401, detail="not connected"),
    ):
        with pytest.raises(HTTPException) as exc_info:
            await provider.sync(db, sync_record)

    assert exc_info.value.status_code == 401


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _mock_scalar_none() -> MagicMock:
    """Return a mock db.execute() result that yields scalar_one_or_none() == None."""
    result = MagicMock()
    result.scalar_one_or_none.return_value = None
    return result
