from __future__ import annotations

import uuid
from datetime import date

from sqlalchemy import inspect

from app.models.weekly_review import ReviewStatus, WeeklyReview


def test_weekly_review_tablename() -> None:
    """WeeklyReview.__tablename__ must be 'weekly_reviews'."""
    assert WeeklyReview.__tablename__ == "weekly_reviews"


def test_weekly_review_has_required_columns() -> None:
    """WeeklyReview model must have all columns defined in DATA_MODEL.md."""
    columns = {c.name for c in inspect(WeeklyReview).columns}
    expected = {
        "id",
        "user_id",
        "week_start",
        "raw_data_json",
        "insights_json",
        "narrative",
        "scores_json",
        "agent_metadata_json",
        "status",
        "created_at",
    }
    assert expected.issubset(columns), f"Missing columns: {expected - columns}"


def test_weekly_review_id_is_uuid() -> None:
    """WeeklyReview.id column type must be UUID."""
    col = inspect(WeeklyReview).columns["id"]
    assert "UUID" in str(col.type).upper()


def test_weekly_review_user_id_is_foreign_key() -> None:
    """WeeklyReview.user_id must reference users.id."""
    col = inspect(WeeklyReview).columns["user_id"]
    fk_targets = {fk.target_fullname for fk in col.foreign_keys}
    assert "users.id" in fk_targets


def test_weekly_review_user_id_not_nullable() -> None:
    """WeeklyReview.user_id must be NOT NULL."""
    col = inspect(WeeklyReview).columns["user_id"]
    assert col.nullable is False


def test_weekly_review_week_start_not_nullable() -> None:
    """WeeklyReview.week_start must be NOT NULL."""
    col = inspect(WeeklyReview).columns["week_start"]
    assert col.nullable is False


def test_weekly_review_raw_data_json_not_nullable() -> None:
    """WeeklyReview.raw_data_json must be NOT NULL."""
    col = inspect(WeeklyReview).columns["raw_data_json"]
    assert col.nullable is False


def test_weekly_review_raw_data_json_is_jsonb() -> None:
    """WeeklyReview.raw_data_json must be JSONB."""
    col = inspect(WeeklyReview).columns["raw_data_json"]
    assert "JSONB" in str(col.type).upper()


def test_weekly_review_insights_json_nullable() -> None:
    """WeeklyReview.insights_json must be NULLABLE."""
    col = inspect(WeeklyReview).columns["insights_json"]
    assert col.nullable is True


def test_weekly_review_narrative_nullable() -> None:
    """WeeklyReview.narrative must be NULLABLE."""
    col = inspect(WeeklyReview).columns["narrative"]
    assert col.nullable is True


def test_weekly_review_scores_json_nullable() -> None:
    """WeeklyReview.scores_json must be NULLABLE."""
    col = inspect(WeeklyReview).columns["scores_json"]
    assert col.nullable is True


def test_weekly_review_agent_metadata_json_nullable() -> None:
    """WeeklyReview.agent_metadata_json must be NULLABLE."""
    col = inspect(WeeklyReview).columns["agent_metadata_json"]
    assert col.nullable is True


def test_weekly_review_status_not_nullable() -> None:
    """WeeklyReview.status must be NOT NULL."""
    col = inspect(WeeklyReview).columns["status"]
    assert col.nullable is False


def test_weekly_review_status_defaults_to_pending() -> None:
    """WeeklyReview.status must default to 'pending'."""
    col = inspect(WeeklyReview).columns["status"]
    assert col.default is not None
    assert col.default.arg == ReviewStatus.PENDING  # type: ignore[attr-defined]


def test_weekly_review_created_at_not_nullable() -> None:
    """WeeklyReview.created_at must be NOT NULL."""
    col = inspect(WeeklyReview).columns["created_at"]
    assert col.nullable is False


def test_weekly_review_created_at_is_datetime_tz() -> None:
    """WeeklyReview.created_at must be timezone-aware."""
    from sqlalchemy import DateTime as SADateTime

    col = inspect(WeeklyReview).columns["created_at"]
    assert isinstance(col.type, SADateTime)
    assert col.type.timezone is True


def test_weekly_review_has_status_check_constraint() -> None:
    """WeeklyReview must have a CHECK constraint on status."""
    constraints = {c.name for c in WeeklyReview.__table__.constraints}  # type: ignore[attr-defined]
    assert "ck_weekly_reviews_status" in constraints


def test_weekly_review_has_user_week_index() -> None:
    """WeeklyReview must have idx_weekly_review_user_week index."""
    indexes = {idx.name for idx in WeeklyReview.__table__.indexes}  # type: ignore[attr-defined]
    assert "idx_weekly_review_user_week" in indexes


def test_weekly_review_defaults() -> None:
    """Instantiating WeeklyReview sets status=pending, nullable fields to None."""
    obj = WeeklyReview(
        user_id=uuid.uuid4(),
        week_start=date(2026, 4, 14),
        raw_data_json={},
    )
    assert obj.status == ReviewStatus.PENDING
    assert obj.narrative is None
    assert obj.scores_json is None
    assert obj.insights_json is None
    assert obj.agent_metadata_json is None


def test_weekly_review_repr() -> None:
    """WeeklyReview.__repr__ must include user_id and week_start."""
    uid = uuid.uuid4()
    obj = WeeklyReview(
        user_id=uid,
        week_start=date(2026, 4, 14),
        raw_data_json={},
    )
    r = repr(obj)
    assert str(uid) in r
    assert "2026-04-14" in r


def test_review_status_enum_values() -> None:
    """ReviewStatus enum must have pending/generating/complete/failed."""
    assert ReviewStatus.PENDING.value == "pending"
    assert ReviewStatus.GENERATING.value == "generating"
    assert ReviewStatus.COMPLETE.value == "complete"
    assert ReviewStatus.FAILED.value == "failed"
