from __future__ import annotations

import time

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from jose import JWTError

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    decrypt_oauth_token,
    encrypt_oauth_token,
)


# --- Fernet encryption tests ---


def test_encrypt_token_returns_different_string() -> None:
    """Encrypted output must differ from the plaintext input."""
    plain = "my-oauth-token-abc123"
    encrypted = encrypt_oauth_token(plain)
    assert encrypted != plain


def test_decrypt_token_returns_original() -> None:
    """Roundtrip encrypt → decrypt must return the original plaintext."""
    plain = "ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
    encrypted = encrypt_oauth_token(plain)
    decrypted = decrypt_oauth_token(encrypted)
    assert decrypted == plain


def test_encrypt_empty_string_raises() -> None:
    """Encrypting an empty string must raise ValueError."""
    with pytest.raises(ValueError, match="empty"):
        encrypt_oauth_token("")


@given(st.text(min_size=1, max_size=500))
@settings(max_examples=50)
def test_fernet_roundtrip_with_random_input(value: str) -> None:
    """Property: encrypt → decrypt is identity for any non-empty string."""
    encrypted = encrypt_oauth_token(value)
    assert decrypt_oauth_token(encrypted) == value


# --- JWT tests ---


def test_create_access_token_returns_string() -> None:
    """create_access_token must return a non-empty JWT string."""
    token = create_access_token(subject="user@example.com")
    assert isinstance(token, str)
    assert len(token) > 0


def test_decode_access_token_returns_subject() -> None:
    """Decoding a valid access token must return the original subject in 'sub'."""
    email = "user@example.com"
    token = create_access_token(subject=email)
    payload = decode_token(token)
    assert payload["sub"] == email


def test_decode_expired_token_raises() -> None:
    """Decoding an expired token must raise JWTError."""
    token = create_access_token(subject="user@example.com", expires_minutes=-1)
    time.sleep(0.1)
    with pytest.raises(JWTError):
        decode_token(token)


def test_create_refresh_token_has_longer_expiry() -> None:
    """Refresh token 'exp' must be later than access token 'exp'."""
    access = create_access_token(subject="user@example.com")
    refresh = create_refresh_token(subject="user@example.com")
    access_payload = decode_token(access)
    refresh_payload = decode_token(refresh)
    assert refresh_payload["exp"] > access_payload["exp"]
