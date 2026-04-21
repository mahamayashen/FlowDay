"""PII anonymization layer for LLM calls.

Detects, tokenizes, and restores PII in agent deps/outputs so that
no personally identifiable information is sent to LLM providers.
"""

from __future__ import annotations

import dataclasses
import re
import uuid
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any

from pydantic import BaseModel

# ---------------------------------------------------------------------------
# Known PII field names → anonymization category
# ---------------------------------------------------------------------------

PII_FIELD_NAMES: dict[str, str] = {
    "task_title": "task",
    "project_name": "project",
    "title": "task",
    "most_active_project": "project",
    "most_active_repo": "repo",
    "client_name": "client",
}

# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class PIIMatch:
    """A single PII match found in text."""

    start: int
    end: int
    value: str
    category: str


@dataclass(frozen=True)
class AnonymizationRecord:
    """Audit record for one anonymization event (no PII values stored)."""

    category: str
    field_path: str
    token: str


# ---------------------------------------------------------------------------
# PIIDetector
# ---------------------------------------------------------------------------

_EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b")
_FINANCIAL_RE = re.compile(r"\$\d[\d,]*\.?\d*")


class PIIDetector:
    """Detects PII in text using compiled regex patterns."""

    _patterns: list[tuple[re.Pattern[str], str]] = [
        (_EMAIL_RE, "email"),
        (_FINANCIAL_RE, "financial"),
    ]

    def detect(self, text: str) -> list[PIIMatch]:
        """Return all PII matches in *text*, sorted by start position."""
        matches: list[PIIMatch] = []
        for pattern, category in self._patterns:
            for m in pattern.finditer(text):
                matches.append(
                    PIIMatch(
                        start=m.start(),
                        end=m.end(),
                        value=m.group(),
                        category=category,
                    )
                )
        matches.sort(key=lambda m: m.start)
        return matches


# ---------------------------------------------------------------------------
# PIIAnonymizer
# ---------------------------------------------------------------------------


class PIIAnonymizer:
    """Stateful anonymizer that maintains a token<->original bidirectional map."""

    def __init__(self) -> None:
        self._forward: dict[str, str] = {}  # original → token
        self._reverse: dict[str, str] = {}  # token → original
        self._counters: dict[str, int] = {}
        self._audit_log: list[AnonymizationRecord] = []
        self._detector = PIIDetector()

    def anonymize_value(self, value: str, category: str, field_path: str = "") -> str:
        """Replace *value* with a deterministic ``[CATEGORY_N]`` token.

        Idempotent: the same *value* always maps to the same token.
        """
        if value in self._forward:
            return self._forward[value]

        upper = category.upper()
        count = self._counters.get(upper, 0) + 1
        self._counters[upper] = count
        token = f"[{upper}_{count}]"

        self._forward[value] = token
        self._reverse[token] = value
        self._audit_log.append(
            AnonymizationRecord(category=upper, field_path=field_path, token=token)
        )
        return token

    def anonymize_text(self, text: str) -> str:
        """Detect regex-based PII in *text* and replace inline."""
        matches = self._detector.detect(text)
        if not matches:
            return text

        # Process from right to left so indices stay valid.
        for m in reversed(matches):
            token = self.anonymize_value(m.value, m.category)
            text = text[: m.start] + token + text[m.end :]
        return text

    def deanonymize_text(self, text: str) -> str:
        """Restore all tokens in *text* with their original values.

        Tokens are replaced longest-first to prevent partial matches.
        """
        if not self._reverse:
            return text

        for token in sorted(self._reverse, key=len, reverse=True):
            text = text.replace(token, self._reverse[token])
        return text

    def get_audit_summary(self) -> dict[str, int]:
        """Return category → count mapping. Contains no PII values."""
        return dict(self._counters)


# ---------------------------------------------------------------------------
# Helpers for anonymize_deps
# ---------------------------------------------------------------------------


def _anonymize_value_by_field(
    field_name: str,
    value: Any,
    anonymizer: PIIAnonymizer,
    parent_path: str,
) -> Any:
    field_path = f"{parent_path}.{field_name}" if parent_path else field_name

    skip_types = (bool, int, float, uuid.UUID, date, datetime)
    if value is None or isinstance(value, skip_types):
        return value

    if isinstance(value, BaseModel):
        return _anonymize_model(value, anonymizer, field_path)

    if isinstance(value, list):
        return _anonymize_list(field_name, value, anonymizer, field_path)

    if isinstance(value, dict):
        return _anonymize_dict(field_name, value, anonymizer, field_path)

    if isinstance(value, str):
        if field_name in PII_FIELD_NAMES:
            return anonymizer.anonymize_value(
                value, PII_FIELD_NAMES[field_name], field_path
            )
        return anonymizer.anonymize_text(value)

    return value


def _anonymize_list(
    field_name: str,
    items: list[Any],
    anonymizer: PIIAnonymizer,
    parent_path: str,
) -> list[Any]:
    result: list[Any] = []
    for i, item in enumerate(items):
        item_path = f"{parent_path}[{i}]"
        if isinstance(item, BaseModel):
            result.append(_anonymize_model(item, anonymizer, item_path))
        elif isinstance(item, str):
            if field_name in PII_FIELD_NAMES:
                result.append(
                    anonymizer.anonymize_value(
                        item, PII_FIELD_NAMES[field_name], item_path
                    )
                )
            else:
                result.append(anonymizer.anonymize_text(item))
        else:
            result.append(item)
    return result


def _anonymize_dict(
    field_name: str,
    d: dict[str, Any],
    anonymizer: PIIAnonymizer,
    parent_path: str,
) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for k, v in d.items():
        if isinstance(v, str):
            result[k] = anonymizer.anonymize_text(v)
        else:
            result[k] = v
    return result


def _anonymize_model(
    model: BaseModel,
    anonymizer: PIIAnonymizer,
    parent_path: str,
) -> BaseModel:
    updates: dict[str, Any] = {}
    for name in type(model).model_fields:
        value = getattr(model, name)
        new_value = _anonymize_value_by_field(name, value, anonymizer, parent_path)
        if new_value is not value:
            updates[name] = new_value
    if updates:
        return model.model_copy(update=updates)
    return model


# ---------------------------------------------------------------------------
# Public entry points
# ---------------------------------------------------------------------------


def anonymize_deps(deps: Any, anonymizer: PIIAnonymizer) -> Any:
    """Deep-copy and anonymize agent deps.

    Supports both dataclasses (with nested Pydantic fields) and
    Pydantic BaseModel instances.
    """
    if isinstance(deps, BaseModel):
        return _anonymize_model(deps, anonymizer, parent_path="")

    if dataclasses.is_dataclass(deps) and not isinstance(deps, type):
        kwargs: dict[str, Any] = {}
        for f in dataclasses.fields(deps):
            value = getattr(deps, f.name)
            kwargs[f.name] = _anonymize_value_by_field(
                f.name, value, anonymizer, parent_path=""
            )
        return type(deps)(**kwargs)

    return deps


def deanonymize_output[T: BaseModel](output: T, anonymizer: PIIAnonymizer) -> T:
    """Restore anonymization tokens in a Pydantic BaseModel output."""
    updates: dict[str, Any] = {}
    for name in type(output).model_fields:
        value = getattr(output, name)
        if isinstance(value, str):
            updates[name] = anonymizer.deanonymize_text(value)
        elif isinstance(value, list):
            updates[name] = [
                (
                    deanonymize_output(item, anonymizer)
                    if isinstance(item, BaseModel)
                    else (
                        anonymizer.deanonymize_text(item)
                        if isinstance(item, str)
                        else item
                    )
                )
                for item in value
            ]
        elif isinstance(value, BaseModel):
            updates[name] = deanonymize_output(value, anonymizer)
        else:
            updates[name] = value
    return output.model_copy(update=updates)
