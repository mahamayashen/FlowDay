from __future__ import annotations

import uuid
from datetime import date, datetime, timezone

import pytest
from pydantic_ai.models.test import TestModel


@pytest.fixture
def sample_github_sync():
    from app.agents.schemas import GitHubSyncData

    return GitHubSyncData(
        last_synced_at=datetime(2026, 4, 14, 8, 0, tzinfo=timezone.utc),
        sync_config={"repo_count": 3, "most_active_repo": "FlowDay"},
    )


@pytest.mark.asyncio
async def test_code_analyst_result_conforms_to_schema(sample_github_sync):
    """Agent with TestModel returns a valid CodeAnalystResult schema."""
    from app.agents.code_analyst import code_analyst
    from app.agents.schemas import CodeAnalystDeps, CodeAnalystResult

    deps = CodeAnalystDeps(
        user_id=uuid.uuid4(),
        analysis_date=date(2026, 4, 14),
        github_sync=sample_github_sync,
    )

    with code_analyst.override(model=TestModel()):
        result = await code_analyst.run("Analyze code activity", deps=deps)

    output = result.output
    assert isinstance(output, CodeAnalystResult)
    assert isinstance(output.data_available, bool)
    assert output.commits_count >= 0
    assert output.pull_requests_count >= 0
    assert isinstance(output.insights, list)


@pytest.mark.asyncio
async def test_code_analyst_no_github_sync():
    """Agent returns data_available=False when github_sync is None."""
    from app.agents.code_analyst import code_analyst
    from app.agents.schemas import CodeAnalystDeps, CodeAnalystResult

    deps = CodeAnalystDeps(
        user_id=uuid.uuid4(),
        analysis_date=date(2026, 4, 14),
        github_sync=None,
    )

    with code_analyst.override(model=TestModel()):
        result = await code_analyst.run("Analyze code activity", deps=deps)

    output = result.output
    assert isinstance(output, CodeAnalystResult)
    assert output.data_available is False
