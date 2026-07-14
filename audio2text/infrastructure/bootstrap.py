"""
Bootstrap orchestrator — wires core-cenf managers in dependency order.

Spec: "ConfigManager (M01) → LoggerManager (M02) → ..."
Slice 1 wires only M01 + M02. Subsequent slices add M03–M18.

Golden rule: only audio2text/infrastructure/ may import cenf_core.
"""

from __future__ import annotations

from typing import Any

from cenf_core.config import BaseSchema, ConfigManager
from cenf_core.logging import LogProfile, LoggerManager

from audio2text.infrastructure.registry import ManagerRegistry


class ConfigError(Exception):
    """Raised when bootstrap cannot proceed due to invalid configuration.

    Halts the manager chain — no half-init state is possible.
    """


class AppConfigSchema(BaseSchema):
    """Minimal config schema for Audio2Text bootstrap."""

    app_name: str = "audio2text"
    log_level: str = "INFO"
    language: str = "es"


def bootstrap(config_dict: dict[str, Any]) -> ManagerRegistry:
    """Wire managers in dependency order and return a populated registry.

    Args:
        config_dict: Configuration values to seed ConfigManager defaults.

    Returns:
        ManagerRegistry with M01 ConfigManager and M02 LoggerManager.

    Raises:
        ConfigError: If config_dict is None (halt — no half-init state).
    """
    if config_dict is None:
        raise ConfigError("config_dict must not be None — bootstrap halted")

    registry = ManagerRegistry()

    # M01: ConfigManager — must be first (other managers depend on it)
    config_manager = ConfigManager(
        schema_class=AppConfigSchema,
        defaults=config_dict,
    )
    registry.register("config", config_manager)

    # M02: LoggerManager — depends on config for log level/profile
    log_level = config_manager.get("log_level", "INFO")
    profile = _resolve_log_profile(log_level)
    logger_manager = LoggerManager(profile=profile)
    registry.register("logger", logger_manager)

    return registry


def _resolve_log_profile(log_level: str) -> LogProfile:
    """Map a log_level string to a LogProfile enum value."""
    if log_level.upper() == "DEBUG":
        return LogProfile.DEVELOPMENT
    return LogProfile.PRODUCTION
