from __future__ import annotations

import base64
import hashlib
from datetime import datetime, timedelta, timezone

from cryptography.fernet import Fernet
from jose import JWTError, jwt

from app.core.config import settings

ALGORITHM = "HS256"


def _get_fernet() -> Fernet:
    """Derive a Fernet key from SECRET_KEY."""
    key = hashlib.sha256(settings.SECRET_KEY.encode()).digest()
    fernet_key = base64.urlsafe_b64encode(key)
    return Fernet(fernet_key)


def encrypt_oauth_token(plain: str) -> str:
    """Encrypt an OAuth token for storage at rest."""
    if not plain:
        raise ValueError("Token must not be empty")
    f = _get_fernet()
    return f.encrypt(plain.encode()).decode()


def decrypt_oauth_token(encrypted: str) -> str:
    """Decrypt a stored OAuth token."""
    f = _get_fernet()
    return f.decrypt(encrypted.encode()).decode()


def create_access_token(
    subject: str, extra: dict | None = None, expires_minutes: int | None = None
) -> str:
    """Create a JWT access token."""
    if expires_minutes is None:
        expires_minutes = settings.ACCESS_TOKEN_EXPIRE_MINUTES
    expire = datetime.now(timezone.utc) + timedelta(minutes=expires_minutes)
    to_encode: dict = {"sub": subject, "exp": expire}
    if extra:
        to_encode.update(extra)
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(subject: str) -> str:
    """Create a JWT refresh token with longer expiry."""
    expire = datetime.now(timezone.utc) + timedelta(
        days=settings.REFRESH_TOKEN_EXPIRE_DAYS
    )
    to_encode: dict = {"sub": subject, "exp": expire, "type": "refresh"}
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    """Decode and validate a JWT token. Raises JWTError on failure."""
    try:
        payload: dict = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        raise
    return payload
