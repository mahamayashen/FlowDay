from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.external_sync import ExternalSync
from app.models.project import Project
from app.models.task import Task
from app.services.github_sync import (
    fetch_github_commits,
    fetch_github_pull_requests,
    fetch_github_repos,
    get_valid_github_access_token,
)
from app.services.sync_provider import BaseSyncProvider, provider_registry

_SENTINEL_PROJECT_NAME = "GitHub"
_SENTINEL_PROJECT_COLOR = "#24292e"
_SYNC_DAYS_BACK = 7


class GitHubSyncProvider(BaseSyncProvider):
    """Syncs GitHub commit and PR data as Task rows under a sentinel project."""

    async def sync(self, db: AsyncSession, sync_record: ExternalSync) -> None:
        """Fetch GitHub activity and upsert it as Task rows for the Code Analyst."""
        access_token = await get_valid_github_access_token(db, sync_record)

        repos = await fetch_github_repos(access_token)

        project = await _get_or_create_sentinel_project(db, sync_record.user_id)

        # Delete existing GitHub tasks before re-creating (full replace)
        await _delete_existing_github_tasks(db, sync_record.user_id)

        now = datetime.now(UTC)
        since = (now - timedelta(days=_SYNC_DAYS_BACK)).isoformat()
        until = now.isoformat()

        for repo in repos:
            owner: str = repo["owner"]["login"]
            repo_name: str = repo["name"]
            full_name: str = repo.get("full_name", f"{owner}/{repo_name}")

            commits = await fetch_github_commits(
                access_token, owner, repo_name, since, until
            )
            for commit in commits:
                sha: str = commit.get("sha", "")
                commit_info: dict[str, Any] = commit.get("commit", {})
                message: str = commit_info.get("message", "").split("\n")[0]
                author_info: dict[str, Any] = commit_info.get("author", {})
                author_date: str = author_info.get("date", "")

                description = json.dumps(
                    {
                        "type": "commit",
                        "repo": full_name,
                        "sha": sha,
                        "author": author_info.get("name", ""),
                        "date": author_date,
                        "message": commit_info.get("message", ""),
                    }
                )
                task = Task(
                    project_id=project.id,
                    title=f"{repo_name}: {sha[:7]} — {message}"[:200],
                    description=description,
                )
                db.add(task)

            prs = await fetch_github_pull_requests(access_token, owner, repo_name)
            for pr in prs:
                pr_number: int = pr.get("number", 0)
                pr_title: str = pr.get("title", "")

                description = json.dumps(
                    {
                        "type": "pull_request",
                        "repo": full_name,
                        "number": pr_number,
                        "title": pr_title,
                        "state": pr.get("state", ""),
                        "created_at": pr.get("created_at", ""),
                        "merged_at": pr.get("merged_at"),
                    }
                )
                task = Task(
                    project_id=project.id,
                    title=f"{repo_name}: PR #{pr_number} — {pr_title}"[:200],
                    description=description,
                )
                db.add(task)

        await db.flush()


async def _get_or_create_sentinel_project(
    db: AsyncSession,
    user_id: Any,
) -> Project:
    """Return the user's GitHub sentinel project, creating it if needed."""
    result = await db.execute(
        select(Project).where(
            Project.user_id == user_id,
            Project.name == _SENTINEL_PROJECT_NAME,
        )
    )
    project = result.scalar_one_or_none()
    if project is None:
        project = Project(
            user_id=user_id,
            name=_SENTINEL_PROJECT_NAME,
            color=_SENTINEL_PROJECT_COLOR,
        )
        db.add(project)
        await db.flush()
    return project


async def _delete_existing_github_tasks(
    db: AsyncSession,
    user_id: Any,
) -> None:
    """Delete all Task rows under the GitHub sentinel project for this user."""
    task_ids_result = await db.execute(
        select(Task.id)
        .join(Project, Task.project_id == Project.id)
        .where(
            Project.user_id == user_id,
            Project.name == _SENTINEL_PROJECT_NAME,
        )
    )
    task_ids = [row[0] for row in task_ids_result.all()]
    if not task_ids:
        return
    await db.execute(delete(Task).where(Task.id.in_(task_ids)))


# Register with the global provider registry
provider_registry.register("github", GitHubSyncProvider)
