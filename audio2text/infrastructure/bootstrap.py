"""
Bootstrap orchestrator — wires core-cenf managers in dependency order.

Spec: "ConfigManager (M01) → LoggerManager (M02) → SecretManager (M03)
       → ErrorHandlingManager (M04) → ..."
Slice 2 adds M03 + M04.

Golden rule: only audio2text/infrastructure/ may import core_infrastructure.
"""

from __future__ import annotations

from typing import Any

from core_infrastructure.common.errors import ValidationError
from core_infrastructure.config import InMemoryConfigAdapter
from core_infrastructure.errors import CapturingErrorAdapter
from core_infrastructure.logger import InMemoryLoggerAdapter
from core_infrastructure.secrets import InMemorySecretAdapter

from audio2text.infrastructure.registry import ManagerRegistry


def bootstrap(config_dict: dict[str, Any] | None) -> ManagerRegistry:
    """Wire managers in dependency order and return a populated registry.

    Order: M01 Config → M02 Logger → M03 Secrets → M04 Errors.

    Args:
        config_dict: Configuration values to seed InMemoryConfigAdapter.
            Must not be None.

    Returns:
        ManagerRegistry with M01–M04 wired.

    Raises:
        ValidationError: If config_dict is None (halt — no half-init state).
    """
    if config_dict is None:
        raise ValidationError(
            "config_dict must not be None — bootstrap halted",
            details={"phase": "bootstrap", "manager": "config"},
        )

    registry = ManagerRegistry()

    # M01: ConfigManager — must be first (all other managers depend on it)
    config = InMemoryConfigAdapter(initial_data=config_dict)
    registry.register("config", config)

    # M02: LoggerManager — depends on config
    logger = InMemoryLoggerAdapter()
    registry.register("logger", logger)

    # M03: SecretManager — depends on config for SecretConfig
    secrets = InMemorySecretAdapter(config=None)
    registry.register("secrets", secrets)

    # M04: ErrorHandlingManager — depends on config + logger + observability
    errors = CapturingErrorAdapter(config=config, logger=logger, observability=None)
    registry.register("errors", errors)

    return registry