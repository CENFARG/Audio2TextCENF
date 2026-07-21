"""
ManagerRegistry — typed accessors for core-cenf managers.

Single source of truth for manager instances after bootstrap.
Only audio2text/infrastructure/ may import core_infrastructure directly.
"""

from __future__ import annotations

from typing import Any


class ManagerRegistry:
    """Typed registry holding references to wired core-cenf managers.

    Attributes:
        init_order: Ordered list of manager keys reflecting bootstrap sequence.
    """

    def __init__(self) -> None:
        self._managers: dict[str, Any] = {}
        self.init_order: list[str] = []

    def register(self, key: str, manager: Any) -> None:
        """Register a manager under a key and record its init order."""
        self._managers[key] = manager
        self.init_order.append(key)

    def get_config(self) -> Any:
        """Return the ConfigManager (M01) instance."""
        return self._managers.get("config")

    def get_logger(self) -> Any:
        """Return the LoggerManager (M02) instance."""
        return self._managers.get("logger")

    def get_secrets(self) -> Any:
        """Return the SecretManager (M03) instance."""
        return self._managers.get("secrets")

    def get_errors(self) -> Any:
        """Return the ErrorHandlingManager (M04) instance."""
        return self._managers.get("errors")

    def get_observability(self) -> Any:
        """Return the ObservabilityManager (M05) instance."""
        return self._managers.get("observability")

    def get_cache(self) -> Any:
        """Return the CacheManager (M07) instance."""
        return self._managers.get("cache")

    def get_i18n(self) -> Any:
        """Return the I18nManager (M17) instance."""
        return self._managers.get("i18n")

    def get(self, key: str) -> Any:
        """Generic accessor for any registered manager."""
        return self._managers.get(key)
