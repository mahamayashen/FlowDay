from __future__ import annotations

from datetime import UTC, datetime

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    encrypt_oauth_token,
)
from app.models.user import User
from app.schemas.user import (
    OAuthCallbackRequest,
    RefreshRequest,
    TokenResponse,
    UserResponse,
)

router = APIRouter(prefix="/auth", tags=["auth"])


# ---------------------------------------------------------------------------
# OAuth helpers
# ---------------------------------------------------------------------------


async def _handle_oauth_callback(
    *,
    provider: str,
    oauth_token: str,
    email: str,
    name: str,
    db: AsyncSession,
) -> TokenResponse:
    """Create or update a user from an OAuth callback, return JWT pair.

    Uses PostgreSQL ON CONFLICT (upsert) to atomically handle concurrent
    requests for the same email without race conditions.
    """
    encrypted_token = encrypt_oauth_token(oauth_token)
    token_field = (
        {"google_oauth_token": encrypted_token}
        if provider == "google"
        else {"github_oauth_token": encrypted_token}
    )

    now = datetime.now(UTC)
    stmt = (
        insert(User)
        .values(
            email=email,
            name=name,
            created_at=now,
            updated_at=now,
            **token_field,
        )
        .on_conflict_do_update(
            index_elements=["email"],
            set_={**token_field, "updated_at": now},
        )
        .returning(User)
    )
    result = await db.execute(stmt)
    user = result.scalar_one()
    await db.commit()

    access = create_access_token(subject=user.email)
    refresh = create_refresh_token(subject=user.email)
    return TokenResponse(access_token=access, refresh_token=refresh)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@router.post("/google/callback", response_model=TokenResponse)
async def google_callback(
    body: OAuthCallbackRequest, db: AsyncSession = Depends(get_db)
) -> TokenResponse:
    """Exchange Google OAuth authorization code for JWT token pair."""
    if settings.GOOGLE_CLIENT_ID is None or settings.GOOGLE_CLIENT_SECRET is None:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Google OAuth is not configured",
        )

    async with httpx.AsyncClient() as client:
        # Exchange code for access token
        token_resp = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "code": body.code,
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "redirect_uri": settings.GOOGLE_REDIRECT_URI,
                "grant_type": "authorization_code",
            },
        )
        if token_resp.status_code != 200:
            import logging
            logging.error(
                "Google token exchange failed: status=%s body=%s redirect_uri=%s",
                token_resp.status_code, token_resp.text, settings.GOOGLE_REDIRECT_URI,
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=(
                    "Failed to exchange Google authorization code: "
                    f"{token_resp.text}"
                ),
            )
        token_data = token_resp.json()

        # Google can return 200 with an error field
        if "error" in token_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Google OAuth error: {token_data['error']}",
            )
        google_access_token: str = token_data["access_token"]

        # Fetch user info
        userinfo_resp = await client.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {google_access_token}"},
        )
        if userinfo_resp.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Failed to fetch Google user info",
            )
        userinfo = userinfo_resp.json()

    return await _handle_oauth_callback(
        provider="google",
        oauth_token=google_access_token,
        email=userinfo["email"],
        name=userinfo.get("name", userinfo["email"]),
        db=db,
    )


@router.post("/github/callback", response_model=TokenResponse)
async def github_callback(
    body: OAuthCallbackRequest, db: AsyncSession = Depends(get_db)
) -> TokenResponse:
    """Exchange GitHub OAuth authorization code for JWT token pair."""
    if settings.GITHUB_CLIENT_ID is None or settings.GITHUB_CLIENT_SECRET is None:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="GitHub OAuth is not configured",
        )

    async with httpx.AsyncClient() as client:
        # Exchange code for access token
        token_resp = await client.post(
            "https://github.com/login/oauth/access_token",
            data={
                "code": body.code,
                "client_id": settings.GITHUB_CLIENT_ID,
                "client_secret": settings.GITHUB_CLIENT_SECRET,
                "redirect_uri": settings.GITHUB_REDIRECT_URI,
            },
            headers={"Accept": "application/json"},
        )
        if token_resp.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Failed to exchange GitHub authorization code",
            )
        token_data = token_resp.json()

        import logging
        logging.error(
            "GitHub token exchange: status=%s body=%s redirect_uri=%s",
            token_resp.status_code,
            token_resp.text,
            settings.GITHUB_REDIRECT_URI,
        )
        # GitHub can return 200 with an error field (e.g. bad_verification_code)
        if "error" in token_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"GitHub OAuth error: {token_data['error']}",
            )
        github_access_token: str = token_data["access_token"]

        # Fetch user info
        user_resp = await client.get(
            "https://api.github.com/user",
            headers={
                "Authorization": f"Bearer {github_access_token}",
                "Accept": "application/vnd.github+json",
            },
        )
        if user_resp.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Failed to fetch GitHub user info",
            )
        gh_user = user_resp.json()

        # GitHub email may be private — fetch from /user/emails
        email = gh_user.get("email")
        if not email:
            emails_resp = await client.get(
                "https://api.github.com/user/emails",
                headers={
                    "Authorization": f"Bearer {github_access_token}",
                    "Accept": "application/vnd.github+json",
                },
            )
            if emails_resp.status_code == 200:
                for entry in emails_resp.json():
                    if entry.get("primary") and entry.get("verified"):
                        email = entry["email"]
                        break

        if not email:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not retrieve email from GitHub",
            )

    return await _handle_oauth_callback(
        provider="github",
        oauth_token=github_access_token,
        email=email,
        name=gh_user.get("name") or gh_user.get("login", email),
        db=db,
    )


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)) -> User:
    """Return the currently authenticated user."""
    return current_user


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    body: RefreshRequest, db: AsyncSession = Depends(get_db)
) -> TokenResponse:
    """Exchange a valid refresh token for a new access token."""
    try:
        payload = decode_token(body.refresh_token)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    # Reject access tokens used on the refresh endpoint
    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token is not a refresh token",
        )

    email: str | None = payload.get("sub")
    if email is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    # Verify user still exists (e.g. not deleted/deactivated)
    result = await db.execute(select(User).where(User.email == email))
    if result.scalar_one_or_none() is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User no longer exists",
        )

    new_access = create_access_token(subject=email)
    return TokenResponse(
        access_token=new_access,
        refresh_token=body.refresh_token,
        token_type="bearer",
    )
