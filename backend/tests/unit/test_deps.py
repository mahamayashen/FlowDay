from __future__ import annotations

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException

from app.core.deps import get_current_user
from app.core.security import create_access_token


def _make_fake_user(email: str = "test@example.com") -> MagicMock:
    """Create a mock User object."""
    user = MagicMock()
    user.id = uuid.uuid4()
    user.email = email
    user.name = "Test User"
    user.settings_json = {}
    user.created_at = datetime.now(UTC)
    return user


@pytest.mark.asyncio
async def test_get_current_user_returns_user_for_valid_token() -> None:
    """Given a valid JWT with user email as sub, returns the User."""
    email = "test@example.com"
    token = create_access_token(subject=email)
    fake_user = _make_fake_user(email)

    mock_db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = fake_user
    mock_db.execute.return_value = mock_result

    user = await get_current_user(token=token, db=mock_db)
    assert user.email == email


@pytest.mark.asyncio
async def test_get_current_user_raises_401_for_expired_token() -> None:
    """Expired JWT must raise HTTPException with status 401."""
    token = create_access_token(subject="test@example.com", expires_minutes=-1)
    mock_db = AsyncMock()

    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(token=token, db=mock_db)
    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_get_current_user_raises_401_for_invalid_token() -> None:
    """Garbage string must raise HTTPException with status 401."""
    mock_db = AsyncMock()

    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(token="not-a-real-token", db=mock_db)
    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_get_current_user_raises_401_for_missing_sub() -> None:
    """JWT without 'sub' claim must raise HTTPException with status 401."""
    from jose import jwt

    from app.core.config import settings
    from app.core.security import ALGORITHM

    token = jwt.encode({"exp": 9999999999}, settings.SECRET_KEY, algorithm=ALGORITHM)
    mock_db = AsyncMock()

    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(token=token, db=mock_db)
    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_get_current_user_raises_401_for_nonexistent_user() -> None:
    """Valid JWT but user not in DB must raise HTTPException with status 401."""
    token = create_access_token(subject="ghost@example.com")

    mock_db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db.execute.return_value = mock_result

    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(token=token, db=mock_db)
    assert exc_info.value.status_code == 401
