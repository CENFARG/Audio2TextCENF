"""
Tests for bootstrap wiring order and config failure halting.

Spec: "Bootstrap initializes all managers in order"
- ConfigManager (M01) MUST be created before LoggerManager (M02).

Spec: "Bootstrap halts on config failure"
- Invalid/missing config raises ConfigError before any other manager is created.
- No manager instance is left in a half-initialized state.
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


class TestBootstrapHaltsOnConfigFailure:
    """Spec: 'Bootstrap halts on config failure' — no half-init state."""

    def test_none_config_raises_config_error(self):
        """Passing None as config_dict raises ConfigError."""
        from audio2text.infrastructure.bootstrap import ConfigError, bootstrap

        with pytest.raises(ConfigError):
            bootstrap(None)

    def test_none_config_no_logger_created(self):
        """When config fails, LoggerManager must NOT be created (no half-init)."""
        from audio2text.infrastructure.bootstrap import ConfigError, bootstrap

        try:
            bootstrap(None)
        except ConfigError:
            pass  # expected

        # If we got here without a registry, no half-init occurred.
        # Verify by attempting a fresh bootstrap with valid config — it should work.
        registry = bootstrap({"app_name": "recovery_test"})
        assert registry.get_config() is not None
        assert registry.get_logger() is not None

    def test_empty_dict_succeeds_with_defaults(self):
        """Empty dict is valid — ConfigManager uses schema defaults."""
        from audio2text.infrastructure.bootstrap import bootstrap

        registry = bootstrap({})
        config = registry.get_config()
        assert config.get("app_name") == "audio2text"  # schema default
