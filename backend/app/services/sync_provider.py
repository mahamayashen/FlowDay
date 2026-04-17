from __future__ import annotations

import abc

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.external_sync import ExternalSync


class BaseSyncProvider(abc.ABC):
    """Abstract base class for external sync providers."""

    @abc.abstractmethod
    async def sync(self, db: AsyncSession, sync_record: ExternalSync) -> None:
        """Execute sync for the given ExternalSync record."""
        ...


class ProviderRegistry:
    """Registry mapping provider names to BaseSyncProvider subclasses."""

    def __init__(self) -> None:
        self._providers: dict[str, type[BaseSyncProvider]] = {}

    def register(
        self, provider_name: str, provider_class: type[BaseSyncProvider]
    ) -> None:
        """Register a provider class under the given name."""
        self._providers[provider_name] = provider_class

    def get(self, provider_name: str) -> type[BaseSyncProvider] | None:
        """Return the provider class for the given name, or None."""
        return self._providers.get(provider_name)

    def list_providers(self) -> list[str]:
        """Return all registered provider names."""
        return list(self._providers.keys())


# Module-level singleton used by the sync service
provider_registry = ProviderRegistry()
