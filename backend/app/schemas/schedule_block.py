import uuid
from datetime import date as date_type
from datetime import datetime
from decimal import Decimal
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.models.schedule_block import ScheduleBlockSource

_VALID_SOURCES = {s.value for s in ScheduleBlockSource}


class ScheduleBlockCreate(BaseModel):
    """Schema for creating a new schedule block."""

    task_id: uuid.UUID
    date: date_type
    start_hour: Decimal = Field(ge=0, le=24)
    end_hour: Decimal = Field(ge=0, le=24)
    source: str = "manual"

    @model_validator(mode="after")
    def validate_end_gt_start(self) -> Self:
        """end_hour must be greater than start_hour."""
        if self.end_hour <= self.start_hour:
            msg = "end_hour must be greater than start_hour"
            raise ValueError(msg)
        return self

    @field_validator("source")
    @classmethod
    def validate_source(cls, v: str) -> str:
        """Source must be a valid ScheduleBlockSource value."""
        if v not in _VALID_SOURCES:
            msg = f"source must be one of: {', '.join(sorted(_VALID_SOURCES))}"
            raise ValueError(msg)
        return v


class ScheduleBlockUpdate(BaseModel):
    """Schema for updating a schedule block (PUT — resize/move)."""

    date: date_type | None = None
    start_hour: Decimal | None = Field(default=None, ge=0, le=24)
    end_hour: Decimal | None = Field(default=None, ge=0, le=24)
    source: str | None = None

    @model_validator(mode="after")
    def validate_end_gt_start(self) -> Self:
        """When both hours are provided, end_hour must be > start_hour."""
        if (
            self.start_hour is not None
            and self.end_hour is not None
            and self.end_hour <= self.start_hour
        ):
            msg = "end_hour must be greater than start_hour"
            raise ValueError(msg)
        return self

    @field_validator("source")
    @classmethod
    def validate_source(cls, v: str | None) -> str | None:
        """Source must be a valid ScheduleBlockSource value if provided."""
        if v is not None and v not in _VALID_SOURCES:
            msg = f"source must be one of: {', '.join(sorted(_VALID_SOURCES))}"
            raise ValueError(msg)
        return v


class ScheduleBlockResponse(BaseModel):
    """Public schedule block representation."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    task_id: uuid.UUID
    date: date_type
    start_hour: Decimal
    end_hour: Decimal
    source: str
    created_at: datetime
