from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserResponse(BaseModel):
    """Public user representation — never exposes tokens or passwords."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    name: str
    settings_json: dict[str, Any]
    created_at: datetime


class UserCreate(BaseModel):
    """Schema for creating a user (future local auth support)."""

    email: EmailStr
    name: str
    password: str | None = None


class TokenResponse(BaseModel):
    """JWT token pair returned after successful authentication."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    """Request body for token refresh."""

    refresh_token: str


class OAuthCallbackRequest(BaseModel):
    """Request body for OAuth code exchange — keeps the code out of the URL."""

    code: str = Field(min_length=1)
