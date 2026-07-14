"""
Bootstrap orchestrator — wires core-cenf managers in dependency order.

Spec: "ConfigManager (M01) → LoggerManager (M02) → ..."
Slice 1 wires only M01 + M02. Subsequent slices add M03–M18.

Golden rule: only audio2text/infrastructure/ may import core_infrastructure.
"""

from __future__ import annotations

from typing import Any

from core_infrastructure.common.errors import ValidationError
from core_infrastructure.config import InMemoryConfigAdapter
from core_infrastructure.logger import InMemoryLoggerAdapter

from audio2text.infrastructure.registry import ManagerRegistry


def bootstrap(config_dict: dict[str, Any] | None) -> ManagerRegistry:
    """Wire managers in dependency order and return a populated registry.

    Args:
        config_dict: Configuration values to seed InMemoryConfigAdapter.
            Must not be None.

    Returns:
        ManagerRegistry with M01 ConfigManager and M02 LoggerManager.

    Raises:
        ValidationError: If config_dict is None (halt — no half-init state).
    """
    if config_dict is None:
        raise ValidationError(
            "config_dict must not be None — bootstrap halted",
            details={"phase": "bootstrap", "manager": "config"},
        )

    registry = ManagerRegistry()

    # M01: ConfigManager — must be first (other managers depend on it)
    config = InMemoryConfigAdapter(initial_data=config_dict)
    registry.register("config", config)

    # M02: LoggerManager — depends on config
    logger = InMemoryLoggerAdapter()
    registry.register("logger", logger)

    return registry