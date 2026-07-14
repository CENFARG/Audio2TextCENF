"""
RED tests for bootstrap wiring order.

Spec: "Bootstrap initializes all managers in order"
- ConfigManager (M01) MUST be created before LoggerManager (M02).

These tests reference audio2text.infrastructure.bootstrap which does NOT exist yet.
They MUST fail until the GREEN implementation is provided.
"""

import pytest


class TestBootstrapOrder:
    """Verify M01 ConfigManager → M02 LoggerManager instantiation order."""

    def test_bootstrap_returns_registry_with_config_and_logger(self):
        """Bootstrap with valid config_dict returns a registry containing both managers."""
        from audio2text.infrastructure.bootstrap import bootstrap

        config_dict = {"app_name": "audio2text", "log_level": "DEBUG"}
        registry = bootstrap(config_dict)

        assert registry.get_config() is not None
        assert registry.get_logger() is not None

    def test_config_manager_created_before_logger(self):
        """ConfigManager (M01) MUST be instantiated before LoggerManager (M02)."""
        from audio2text.infrastructure.bootstrap import bootstrap

        config_dict = {"app_name": "audio2text", "log_level": "DEBUG"}
        registry = bootstrap(config_dict)

        init_order = registry.init_order
        assert "config" in init_order
        assert "logger" in init_order
        assert init_order.index("config") < init_order.index("logger")

    def test_config_manager_provides_values(self):
        """ConfigManager wired with config_dict returns correct values via get()."""
        from audio2text.infrastructure.bootstrap import bootstrap

        config_dict = {"app_name": "audio2text", "language": "es"}
        registry = bootstrap(config_dict)

        config = registry.get_config()
        assert config.get("app_name") == "audio2text"
        assert config.get("language") == "es"

    def test_logger_manager_returns_named_logger(self):
        """LoggerManager provides a working logger with correct name."""
        from audio2text.infrastructure.bootstrap import bootstrap

        config_dict = {"app_name": "audio2text"}
        registry = bootstrap(config_dict)

        logger = registry.get_logger().get_logger("test.module")
        assert logger.name == "test.module"
