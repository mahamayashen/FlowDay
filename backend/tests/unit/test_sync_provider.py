from __future__ import annotations

import pytest

from app.services.sync_provider import BaseSyncProvider, ProviderRegistry


class _FakeProvider(BaseSyncProvider):
    async def sync(self, db, sync_record) -> None:  # type: ignore[override]
        pass


class _AnotherProvider(BaseSyncProvider):
    async def sync(self, db, sync_record) -> None:  # type: ignore[override]
        pass


def test_base_sync_provider_is_abstract() -> None:
    """BaseSyncProvider cannot be instantiated directly."""
    with pytest.raises(TypeError):
        BaseSyncProvider()  # type: ignore[abstract]


def test_base_sync_provider_sync_is_abstract_method() -> None:
    """BaseSyncProvider.sync must be declared as an abstract method."""
    assert getattr(BaseSyncProvider.sync, "__isabstractmethod__", False) is True


def test_concrete_provider_can_be_instantiated() -> None:
    """A concrete subclass implementing sync() can be instantiated."""
    provider = _FakeProvider()
    assert isinstance(provider, BaseSyncProvider)


def test_provider_registry_register_and_get() -> None:
    """Registered provider can be retrieved by name."""
    registry = ProviderRegistry()
    registry.register("github", _FakeProvider)
    assert registry.get("github") is _FakeProvider


def test_provider_registry_get_unknown_returns_none() -> None:
    """Getting an unregistered provider name returns None."""
    registry = ProviderRegistry()
    assert registry.get("nonexistent") is None


def test_provider_registry_register_overwrites() -> None:
    """Re-registering a name overwrites the previous class."""
    registry = ProviderRegistry()
    registry.register("github", _FakeProvider)
    registry.register("github", _AnotherProvider)
    assert registry.get("github") is _AnotherProvider


def test_provider_registry_list_providers() -> None:
    """list_providers() returns all registered provider names."""
    registry = ProviderRegistry()
    registry.register("github", _FakeProvider)
    registry.register("google_calendar", _AnotherProvider)
    assert set(registry.list_providers()) == {"github", "google_calendar"}
