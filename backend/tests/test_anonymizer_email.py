"""RED tests for module-level ``anonymize_text`` email redaction.

Acceptance criterion:
    ``anonymize_text(text: str) -> str`` must replace any email address
    (RFC 5322 simple form) with the literal ``<EMAIL>`` before the text is
    passed to an LLM, and preserve non-email content byte-for-byte.
"""

from __future__ import annotations

from hypothesis import given, strategies as st

from app.core.anonymizer import anonymize_text


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------


def test_anonymize_text_replaces_email_in_middle_of_text() -> None:
    """An email embedded in surrounding text is replaced with ``<EMAIL>``."""
    original = "Please contact john.doe@example.com for details."
    expected = "Please contact <EMAIL> for details."

    assert anonymize_text(original) == expected


# ---------------------------------------------------------------------------
# Edge case: no email => byte-for-byte identical output
# ---------------------------------------------------------------------------


def test_anonymize_text_returns_unchanged_when_no_email() -> None:
    """Text containing no email is returned byte-for-byte identical."""
    original = "Total hours logged: 6.5 across three projects."

    assert anonymize_text(original) == original


# ---------------------------------------------------------------------------
# Property-based: any string with no '@' must pass through unchanged
# ---------------------------------------------------------------------------


@given(st.text().filter(lambda s: "@" not in s))
def test_anonymize_text_is_identity_for_strings_without_at_sign(text: str) -> None:
    """For any string lacking ``@``, ``anonymize_text`` is the identity function."""
    assert anonymize_text(text) == text
