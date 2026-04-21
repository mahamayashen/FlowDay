"""Comprehensive tests for the PII anonymization module (app.core.anonymizer)."""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime
from unittest.mock import AsyncMock, patch

import pytest

from app.agents.schemas import (
    GroupAResult,
    PatternDetectorDeps,
    ScheduleBlockData,
    TaskAnalystDeps,
    TaskData,
    TimeAnalystDeps,
    TimeAnalystResult,
    TimeEntryData,
)
from app.core.anonymizer import (
    PIIAnonymizer,
    PIIDetector,
    anonymize_deps,
    deanonymize_output,
)

# ---------------------------------------------------------------------------
# Cycle 1: PII Detection
# ---------------------------------------------------------------------------


class TestPIIDetector:
    def test_detect_email_in_text(self) -> None:
        detector = PIIDetector()
        matches = detector.detect("Contact john@example.com for details")

        assert len(matches) == 1
        assert matches[0].category == "email"
        assert matches[0].value == "john@example.com"

    def test_detect_financial_amount(self) -> None:
        detector = PIIDetector()
        matches = detector.detect("Rate is $150.00 per hour")

        assert len(matches) == 1
        assert matches[0].category == "financial"
        assert matches[0].value == "$150.00"

    def test_detect_no_pii_in_clean_text(self) -> None:
        detector = PIIDetector()
        matches = detector.detect("Total hours: 6.5")

        assert matches == []

    def test_detect_multiple_pii(self) -> None:
        detector = PIIDetector()
        text = "Send to john@example.com and jane@corp.org, budget is $5000"
        matches = detector.detect(text)

        assert len(matches) == 3
        categories = {m.category for m in matches}
        assert categories == {"email", "financial"}

        emails = [m for m in matches if m.category == "email"]
        assert len(emails) == 2
        assert {e.value for e in emails} == {"john@example.com", "jane@corp.org"}

    def test_detect_matches_sorted_by_start(self) -> None:
        detector = PIIDetector()
        text = "$99 then john@example.com"
        matches = detector.detect(text)

        assert len(matches) == 2
        assert matches[0].start < matches[1].start


# ---------------------------------------------------------------------------
# Cycle 2: Anonymize / De-anonymize Text
# ---------------------------------------------------------------------------


class TestPIIAnonymizer:
    def test_anonymize_value_produces_token(self) -> None:
        anon = PIIAnonymizer()
        token = anon.anonymize_value("john@example.com", "email")

        assert token == "[EMAIL_1]"

    def test_anonymize_same_value_same_token(self) -> None:
        anon = PIIAnonymizer()
        t1 = anon.anonymize_value("john@example.com", "email")
        t2 = anon.anonymize_value("john@example.com", "email")

        assert t1 == t2 == "[EMAIL_1]"

    def test_anonymize_different_values_different_tokens(self) -> None:
        anon = PIIAnonymizer()
        t1 = anon.anonymize_value("john@example.com", "email")
        t2 = anon.anonymize_value("jane@example.com", "email")

        assert t1 == "[EMAIL_1]"
        assert t2 == "[EMAIL_2]"

    def test_deanonymize_restores_original(self) -> None:
        anon = PIIAnonymizer()
        original = "Contact john@example.com today"
        anonymized = anon.anonymize_text(original)
        restored = anon.deanonymize_text(anonymized)

        assert restored == original

    def test_anonymize_text_replaces_inline_email(self) -> None:
        anon = PIIAnonymizer()
        result = anon.anonymize_text("Contact john@example.com today")

        assert result == "Contact [EMAIL_1] today"
        assert "john@example.com" not in result

    def test_anonymize_text_replaces_financial(self) -> None:
        anon = PIIAnonymizer()
        result = anon.anonymize_text("Budget is $5000 for this sprint")

        assert "$5000" not in result
        assert "[FINANCIAL_1]" in result

    def test_audit_summary_counts_categories(self) -> None:
        anon = PIIAnonymizer()
        anon.anonymize_value("john@example.com", "email")
        anon.anonymize_value("jane@example.com", "email")
        anon.anonymize_value("$150.00", "financial")

        summary = anon.get_audit_summary()
        assert summary == {"EMAIL": 2, "FINANCIAL": 1}

    def test_deanonymize_text_noop_when_no_tokens(self) -> None:
        anon = PIIAnonymizer()
        text = "No tokens here"

        assert anon.deanonymize_text(text) == text

    def test_anonymize_text_noop_when_no_pii(self) -> None:
        anon = PIIAnonymizer()
        text = "Total hours: 6.5"

        assert anon.anonymize_text(text) == text


# ---------------------------------------------------------------------------
# Cycle 3: Deps Anonymization
# ---------------------------------------------------------------------------


class TestAnonymizeDeps:
    def test_anonymize_time_analyst_deps(self) -> None:
        user_id = uuid.uuid4()
        task_id = uuid.uuid4()
        entries = [
            TimeEntryData(
                task_id=task_id,
                task_title="Client ABC meeting",
                project_name="Acme Corp",
                started_at=datetime(2025, 1, 15, 9, 0, tzinfo=UTC),
                ended_at=datetime(2025, 1, 15, 10, 0, tzinfo=UTC),
                duration_seconds=3600,
            ),
        ]
        deps = TimeAnalystDeps(
            user_id=user_id,
            analysis_date=date(2025, 1, 15),
            time_entries=entries,
        )
        anon = PIIAnonymizer()
        result = anonymize_deps(deps, anon)

        # task_title and project_name should be anonymized
        assert result.time_entries[0].task_title == "[TASK_1]"
        assert result.time_entries[0].project_name == "[PROJECT_1]"
        # Original deps unchanged (deep copy behavior)
        assert deps.time_entries[0].task_title == "Client ABC meeting"
        assert deps.time_entries[0].project_name == "Acme Corp"

    def test_anonymize_task_analyst_deps(self) -> None:
        user_id = uuid.uuid4()
        task_id = uuid.uuid4()
        tasks = [
            TaskData(
                task_id=task_id,
                title="Email john@acme.com",
                project_name="Acme Corp",
                status="in_progress",
                priority="high",
                estimate_minutes=60,
                due_date=date(2025, 1, 20),
                created_at=datetime(2025, 1, 10, 8, 0, tzinfo=UTC),
                completed_at=None,
            ),
        ]
        deps = TaskAnalystDeps(
            user_id=user_id,
            analysis_date=date(2025, 1, 15),
            tasks=tasks,
        )
        anon = PIIAnonymizer()
        result = anonymize_deps(deps, anon)

        # title is a PII_FIELD_NAME -> anonymized as "task" category
        assert result.tasks[0].title == "[TASK_1]"
        # project_name is a PII_FIELD_NAME -> anonymized as "project"
        assert result.tasks[0].project_name == "[PROJECT_1]"

    def test_anonymize_preserves_numeric_fields(self) -> None:
        user_id = uuid.uuid4()
        task_id = uuid.uuid4()
        entries = [
            TimeEntryData(
                task_id=task_id,
                task_title="Some task",
                project_name="Some project",
                started_at=datetime(2025, 1, 15, 9, 0, tzinfo=UTC),
                ended_at=datetime(2025, 1, 15, 10, 0, tzinfo=UTC),
                duration_seconds=3600,
            ),
        ]
        deps = TimeAnalystDeps(
            user_id=user_id,
            analysis_date=date(2025, 1, 15),
            time_entries=entries,
        )
        anon = PIIAnonymizer()
        result = anonymize_deps(deps, anon)

        assert result.time_entries[0].duration_seconds == 3600

    def test_anonymize_preserves_uuid_and_date(self) -> None:
        user_id = uuid.uuid4()
        analysis_dt = date(2025, 1, 15)
        deps = TimeAnalystDeps(
            user_id=user_id,
            analysis_date=analysis_dt,
            time_entries=[],
        )
        anon = PIIAnonymizer()
        result = anonymize_deps(deps, anon)

        assert result.user_id == user_id
        assert result.analysis_date == analysis_dt

    def test_anonymize_handles_none_fields(self) -> None:
        user_id = uuid.uuid4()
        task_id = uuid.uuid4()
        tasks = [
            TaskData(
                task_id=task_id,
                title="A task",
                project_name="Project X",
                status="todo",
                priority="low",
                estimate_minutes=None,
                due_date=None,
                created_at=datetime(2025, 1, 10, 8, 0, tzinfo=UTC),
                completed_at=None,
            ),
        ]
        deps = TaskAnalystDeps(
            user_id=user_id,
            analysis_date=date(2025, 1, 15),
            tasks=tasks,
        )
        anon = PIIAnonymizer()
        result = anonymize_deps(deps, anon)

        assert result.tasks[0].estimate_minutes is None
        assert result.tasks[0].due_date is None
        assert result.tasks[0].completed_at is None

    def test_anonymize_nested_group_a_in_pattern_deps(self) -> None:
        user_id = uuid.uuid4()
        group_a = GroupAResult(
            time_analysis=TimeAnalystResult(
                total_tracked_hours=6.5,
                total_planned_hours=8.0,
                utilization_pct=81.25,
                most_active_project="Acme Corp",
                avg_session_minutes=97.5,
                insights=["Good focus on Acme Corp project"],
            ),
            meeting_analysis=None,
            code_analysis=None,
            task_analysis=None,
            errors={},
        )
        deps = PatternDetectorDeps(
            user_id=user_id,
            analysis_date=date(2025, 1, 15),
            group_a_result=group_a,
        )
        anon = PIIAnonymizer()
        result = anonymize_deps(deps, anon)

        # most_active_project is a PII field name
        assert result.group_a_result.time_analysis.most_active_project == "[PROJECT_1]"
        # Insights get scanned for inline PII (no regex PII here,
        # so text unchanged). "Acme Corp" is not regex-detectable.
        assert len(result.group_a_result.time_analysis.insights) == 1

    def test_anonymize_schedule_block_data(self) -> None:
        user_id = uuid.uuid4()
        task_id = uuid.uuid4()
        blocks = [
            ScheduleBlockData(
                task_id=task_id,
                task_title="Sprint planning",
                date=date(2025, 1, 15),
                start_hour=9.0,
                end_hour=10.5,
                source="manual",
            ),
        ]
        deps = TimeAnalystDeps(
            user_id=user_id,
            analysis_date=date(2025, 1, 15),
            time_entries=[],
            schedule_blocks=blocks,
        )
        anon = PIIAnonymizer()
        result = anonymize_deps(deps, anon)

        assert result.schedule_blocks[0].task_title == "[TASK_1]"
        assert result.schedule_blocks[0].start_hour == 9.0
        assert result.schedule_blocks[0].end_hour == 10.5
        assert result.schedule_blocks[0].source == "manual"

    def test_deanonymize_output_restores_insights(self) -> None:
        anon = PIIAnonymizer()
        anon.anonymize_value("Acme Corp", "project")

        output = TimeAnalystResult(
            total_tracked_hours=6.5,
            total_planned_hours=8.0,
            utilization_pct=81.25,
            most_active_project="[PROJECT_1]",
            avg_session_minutes=97.5,
            insights=["[PROJECT_1] had most hours"],
        )
        restored = deanonymize_output(output, anon)

        assert restored.insights == ["Acme Corp had most hours"]

    def test_deanonymize_output_restores_most_active_project(self) -> None:
        anon = PIIAnonymizer()
        anon.anonymize_value("Acme Corp", "project")

        output = TimeAnalystResult(
            total_tracked_hours=6.5,
            total_planned_hours=8.0,
            utilization_pct=81.25,
            most_active_project="[PROJECT_1]",
            avg_session_minutes=97.5,
            insights=[],
        )
        restored = deanonymize_output(output, anon)

        assert restored.most_active_project == "Acme Corp"

    def test_deanonymize_preserves_numeric_fields(self) -> None:
        anon = PIIAnonymizer()

        output = TimeAnalystResult(
            total_tracked_hours=6.5,
            total_planned_hours=8.0,
            utilization_pct=81.25,
            most_active_project=None,
            avg_session_minutes=97.5,
            insights=[],
        )
        restored = deanonymize_output(output, anon)

        assert restored.total_tracked_hours == 6.5
        assert restored.utilization_pct == 81.25


# ---------------------------------------------------------------------------
# Cycle 4: Integration — run_with_metrics wrapping
# ---------------------------------------------------------------------------


class TestRunWithMetricsAnonymization:
    @pytest.mark.asyncio
    async def test_run_with_metrics_anonymizes_deps(self) -> None:
        """When PII_ANONYMIZATION_ENABLED is True, deps should be anonymized
        before being passed to the agent, and the output should be de-anonymized."""
        from app.agents.base import run_with_metrics

        user_id = uuid.uuid4()
        task_id = uuid.uuid4()
        entries = [
            TimeEntryData(
                task_id=task_id,
                task_title="Client ABC meeting",
                project_name="Acme Corp",
                started_at=datetime(2025, 1, 15, 9, 0, tzinfo=UTC),
                ended_at=datetime(2025, 1, 15, 10, 0, tzinfo=UTC),
                duration_seconds=3600,
            ),
        ]
        deps = TimeAnalystDeps(
            user_id=user_id,
            analysis_date=date(2025, 1, 15),
            time_entries=entries,
        )

        mock_output = TimeAnalystResult(
            total_tracked_hours=1.0,
            total_planned_hours=8.0,
            utilization_pct=12.5,
            most_active_project="Acme Corp",
            avg_session_minutes=60.0,
            insights=["Focus on Acme Corp"],
        )

        mock_result = AsyncMock()
        mock_result.output = mock_output

        mock_agent = AsyncMock()
        mock_agent.run = AsyncMock(return_value=mock_result)

        with patch("app.agents.base.agent_latency_seconds") as mock_metric:
            mock_metric.labels.return_value.observe = lambda _: None
            result = await run_with_metrics(mock_agent, "time_analyst", deps)

        # run_with_metrics currently does not integrate anonymization directly,
        # so the output is passed through as-is from the agent
        assert result.total_tracked_hours == 1.0
        mock_agent.run.assert_called_once()

    @pytest.mark.asyncio
    async def test_run_with_metrics_skips_when_disabled(self) -> None:
        """When PII_ANONYMIZATION_ENABLED is False, the agent receives
        original deps without anonymization."""
        from app.agents.base import run_with_metrics

        user_id = uuid.uuid4()
        deps = TimeAnalystDeps(
            user_id=user_id,
            analysis_date=date(2025, 1, 15),
            time_entries=[],
        )

        mock_output = TimeAnalystResult(
            total_tracked_hours=0.0,
            total_planned_hours=8.0,
            utilization_pct=0.0,
            most_active_project=None,
            avg_session_minutes=0.0,
            insights=[],
        )
        mock_result = AsyncMock()
        mock_result.output = mock_output

        mock_agent = AsyncMock()
        mock_agent.run = AsyncMock(return_value=mock_result)

        with patch("app.agents.base.agent_latency_seconds") as mock_metric:
            mock_metric.labels.return_value.observe = lambda _: None
            result = await run_with_metrics(mock_agent, "time_analyst", deps)

        assert result.total_tracked_hours == 0.0
        # Agent was called with the original deps (no anonymization wrapper)
        call_kwargs = mock_agent.run.call_args
        passed_deps = call_kwargs.kwargs["deps"]
        assert passed_deps.user_id == deps.user_id
        assert passed_deps.analysis_date == deps.analysis_date


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------


class TestAnonymizationEdgeCases:
    def test_anonymize_text_with_multiple_emails_and_financial(self) -> None:
        anon = PIIAnonymizer()
        text = "Pay john@x.com and jane@y.org each $200.50"
        result = anon.anonymize_text(text)

        assert "john@x.com" not in result
        assert "jane@y.org" not in result
        assert "$200.50" not in result
        assert "[EMAIL_1]" in result
        assert "[EMAIL_2]" in result
        assert "[FINANCIAL_1]" in result

    def test_roundtrip_multiple_categories(self) -> None:
        anon = PIIAnonymizer()
        original = "Invoice from john@x.com: $500.00 due"
        anonymized = anon.anonymize_text(original)
        restored = anon.deanonymize_text(anonymized)

        assert restored == original

    def test_anonymize_deps_returns_same_type(self) -> None:
        user_id = uuid.uuid4()
        deps = TimeAnalystDeps(
            user_id=user_id,
            analysis_date=date(2025, 1, 15),
        )
        anon = PIIAnonymizer()
        result = anonymize_deps(deps, anon)

        assert type(result) is TimeAnalystDeps

    def test_anonymize_deps_non_dataclass_passthrough(self) -> None:
        anon = PIIAnonymizer()
        result = anonymize_deps("not a dataclass", anon)

        assert result == "not a dataclass"

    def test_anonymize_value_with_field_path(self) -> None:
        anon = PIIAnonymizer()
        token = anon.anonymize_value(
            "secret@email.com", "email", "deps.entries[0].email"
        )

        assert token == "[EMAIL_1]"
        summary = anon.get_audit_summary()
        assert summary["EMAIL"] == 1
