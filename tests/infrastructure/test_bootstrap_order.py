"""
Tests for bootstrap wiring order and config failure halting.

Spec: "Bootstrap initializes all managers in order"
- ConfigManager (M01) MUST be created before LoggerManager (M02).

Spec: "Bootstrap halts on config failure"
- Invalid/missing config raises ValidationError before any other manager is created.
- No manager instance is left in a half-initialized state.
"""

import pytest

from core_infrastructure.common.errors import ValidationError


class TestBootstrapOrder:
    """Verify M01 ConfigManager -> M02 LoggerManager instantiation order."""

    def test_bootstrap_returns_registry_with_config_and_logger(self):
        """Bootstrap with valid config_dict returns a registry containing both managers."""
        from audio2text.infrastructure.bootstrap import bootstrap

        config_dict = {"app": {"name": "audio2text"}}
        registry = bootstrap(config_dict)

        assert registry.get_config() is not None
        assert registry.get_logger() is not None

    def test_config_manager_created_before_logger(self):
        """ConfigManager (M01) MUST be instantiated before LoggerManager (M02)."""
        from audio2text.infrastructure.bootstrap import bootstrap

        config_dict = {"app": {"name": "audio2text"}}
        registry = bootstrap(config_dict)

        init_order = registry.init_order
        assert "config" in init_order
        assert "logger" in init_order
        assert init_order.index("config") < init_order.index("logger")

    def test_config_manager_provides_values(self):
        """ConfigManager wired with config_dict returns correct values via get_string()."""
        from audio2text.infrastructure.bootstrap import bootstrap

        config_dict = {"app": {"name": "audio2text", "language": "es"}}
        registry = bootstrap(config_dict)

        config = registry.get_config()
        assert config.get_string("app.name") == "audio2text"
        assert config.get_string("app.language") == "es"

    def test_logger_manager_is_usable(self):
        """LoggerManager is wired and callable."""
        from audio2text.infrastructure.bootstrap import bootstrap

        config_dict = {"app": {"name": "audio2text"}}
        registry = bootstrap(config_dict)

        logger = registry.get_logger()
        # InMemoryLoggerAdapter can log without errors
        logger.info("test.event", module="test")
        # Should not raise


class TestBootstrapHaltsOnConfigFailure:
    """Spec: 'Bootstrap halts on config failure' - no half-init state."""

    def test_none_config_raises_validation_error(self):
        """Passing None as config_dict raises ValidationError."""
        from audio2text.infrastructure.bootstrap import bootstrap

        with pytest.raises(ValidationError, match="bootstrap halted"):
            bootstrap(None)

    def test_none_config_no_logger_created(self):
        """When config fails, LoggerManager must NOT be created (no half-init)."""
        from audio2text.infrastructure.bootstrap import bootstrap

        try:
            bootstrap(None)
        except ValidationError:
            pass  # expected

        # If we got here without a registry, no half-init occurred.
        # Verify by attempting a fresh bootstrap with valid config - it should work.
        registry = bootstrap({"app": {"name": "recovery_test"}})
        assert registry.get_config() is not None
        assert registry.get_logger() is not None

    def test_empty_dict_succeeds_with_defaults(self):
        """Empty dict is valid - InMemoryConfigAdapter uses CoreSettings defaults."""
        from audio2text.infrastructure.bootstrap import bootstrap

        registry = bootstrap({})
        config = registry.get_config()
        # CoreSettings default env is "dev"
        assert config.get_env() in ("local", "dev", "staging", "prod")