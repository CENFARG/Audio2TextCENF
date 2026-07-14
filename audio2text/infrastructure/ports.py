"""
Port definitions — Protocol types for infrastructure dependencies.

Re-exports cenf_core manager interfaces as typing.Protocols so that
business modules depend on abstractions, not concrete adapters.

Golden rule: only audio2text/infrastructure/ imports cenf_core.
Business code imports from this module instead.
"""

from __future__ import annotations

import logging
from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class ConfigPort(Protocol):
    """Protocol matching cenf_core.ConfigManager public interface."""

    def get(self, key: str, default: Any = None) -> Any: ...
    def set(self, key: str, value: Any) -> None: ...
    def as_dict(self, mask_secrets_flag: bool = True) -> dict[str, Any]: ...


@runtime_checkable
class LoggerPort(Protocol):
    """Protocol matching cenf_core.LoggerManager public interface."""

    def get_logger(self, name: str) -> logging.Logger: ...


@runtime_checkable
class SecretPort(Protocol):
    """Protocol matching cenf_core.SecretManager public interface (Slice 2)."""

    def get(self, key: str) -> str | None: ...
    def set(self, key: str, value: str) -> None: ...
    def delete(self, key: str) -> None: ...
