"""
ManagerRegistry — typed accessors for core-cenf managers.

Single source of truth for manager instances after bootstrap.
Only audio2text/infrastructure/ may import cenf_core directly.
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

    def get(self, key: str) -> Any:
        """Generic accessor for any registered manager."""
        return self._managers.get(key)
