"""
Port definitions — Protocol types for infrastructure dependencies.

Re-exports core_infrastructure manager interfaces so that
business modules depend on abstractions, not concrete adapters.

Golden rule: only audio2text/infrastructure/ imports core_infrastructure.
Business code imports from this module instead.
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class ConfigPort(Protocol):
    """Protocol matching core_infrastructure.config.ConfigManager public interface."""

    def get_env(self) -> str: ...
    def get_string(self, key: str, default_value: str | None = None) -> str: ...
    def get_number(self, key: str, default_value: float | None = None) -> float: ...
    def get_boolean(self, key: str, default_value: bool | None = None) -> bool: ...
    def get_section(self, namespace: str) -> dict[str, Any]: ...


@runtime_checkable
class LoggerPort(Protocol):
    """Protocol matching core_infrastructure.logger.LoggerManager public interface."""

    def info(self, event: str, **kwargs: Any) -> None: ...
    def debug(self, event: str, **kwargs: Any) -> None: ...
    def warn(self, event: str, **kwargs: Any) -> None: ...
    def error(self, event: str, **kwargs: Any) -> None: ...