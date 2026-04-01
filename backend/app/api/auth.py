from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from jose import JWTError
from pydantic import BaseModel

from app.core.deps import get_current_user
from app.core.security import create_access_token, decode_token
from app.models.user import User
from app.schemas.user import TokenResponse, UserResponse

router = APIRouter(prefix="/auth", tags=["auth"])


class RefreshRequest(BaseModel):
    """Request body for token refresh."""

    refresh_token: str


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)) -> User:
    """Return the currently authenticated user."""
    return current_user


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(body: RefreshRequest) -> TokenResponse:
    """Exchange a valid refresh token for a new access token."""
    try:
        payload = decode_token(body.refresh_token)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    email: str | None = payload.get("sub")
    if email is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    new_access = create_access_token(subject=email)
    return TokenResponse(
        access_token=new_access,
        refresh_token=body.refresh_token,
        token_type="bearer",
    )
