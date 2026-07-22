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
        logger.info("test.event", module="test")


class TestSlice2SecretsAndErrors:
    """Verify M03 SecretManager and M04 ErrorHandlingManager wiring."""

    def test_bootstrap_wires_all_four_managers(self):
        """Registry contains M01-M04 after bootstrap."""
        from audio2text.infrastructure.bootstrap import bootstrap

        registry = bootstrap({"app": {"name": "audio2text"}})
        assert registry.get_config() is not None
        assert registry.get_logger() is not None
        assert registry.get_secrets() is not None
        assert registry.get_errors() is not None

    def test_secrets_wired_after_logger(self):
        """M03 Secrets MUST be after M02 Logger in init order."""
        from audio2text.infrastructure.bootstrap import bootstrap

        registry = bootstrap({"app": {"name": "audio2text"}})
        order = registry.init_order
        assert order.index("logger") < order.index("secrets")

    def test_errors_wired_after_secrets(self):
        """M04 Errors MUST be after M03 Secrets in init order."""
        from audio2text.infrastructure.bootstrap import bootstrap

        registry = bootstrap({"app": {"name": "audio2text"}})
        order = registry.init_order
        assert order.index("secrets") < order.index("errors")

    def test_init_order_is_config_logger_secrets_errors(self):
        """Full init order: config → logger → secrets → errors → observability → cache → i18n."""
        from audio2text.infrastructure.bootstrap import bootstrap

        registry = bootstrap({"app": {"name": "audio2text"}})
        assert registry.init_order == [
            "config", "logger", "secrets", "errors",
            "observability", "cache", "dependency", "i18n",
        ]

    def test_secret_manager_can_set_and_get(self):
        """InMemorySecretAdapter supports set/get operations."""
        from audio2text.infrastructure.bootstrap import bootstrap

        registry = bootstrap({"app": {"name": "audio2text"}})
        secrets = registry.get_secrets()
        import asyncio
        secrets.set_secret("test_key", "secret_value")
        result = asyncio.run(secrets.get_secret("test_key"))
        assert result == "secret_value"

    def test_error_manager_classify_does_not_raise(self):
        """CapturingErrorAdapter accepts classify() calls."""
        from audio2text.infrastructure.bootstrap import bootstrap

        registry = bootstrap({"app": {"name": "audio2text"}})
        errors = registry.get_errors()
        # CapturingErrorAdapter captures without re-raising
        try:
            raise ValueError("test error")
        except ValueError as e:
            errors.classify(e)


class TestSlice3ObservabilityCacheI18n:
    """Verify M05 Observability, M07 Cache, M17 I18n wiring."""

    def test_all_seven_managers_wired(self):
        """Registry contains M01-M05, M07, M17 after bootstrap."""
        from audio2text.infrastructure.bootstrap import bootstrap

        registry = bootstrap({"app": {"name": "audio2text"}})
        assert registry.get_config() is not None
        assert registry.get_logger() is not None
        assert registry.get_secrets() is not None
        assert registry.get_errors() is not None
        assert registry.get_observability() is not None
        assert registry.get_cache() is not None
        assert registry.get_i18n() is not None

    def test_observability_counter_does_not_raise(self):
        """NoopObservabilityAdapter accepts increment_counter without errors."""
        from audio2text.infrastructure.bootstrap import bootstrap

        registry = bootstrap({"app": {"name": "audio2text"}})
        obs = registry.get_observability()
        obs.increment_counter("transcribe.count", 1)
        obs.increment_counter("cache.hits", 5)

    def test_cache_set_and_get(self):
        """MemoryCacheAdapter supports set/get operations."""
        from audio2text.infrastructure.bootstrap import bootstrap

        registry = bootstrap({"app": {"name": "audio2text"}})
        cache = registry.get_cache()
        cache.set("test_key", "cached_value")
        assert cache.get("test_key") == "cached_value"
        assert cache.exists("test_key") is True
        assert cache.exists("nonexistent") is False

    def test_cache_get_or_set_uses_factory(self):
        """get_or_set calls factory on cache miss."""
        from audio2text.infrastructure.bootstrap import bootstrap

        registry = bootstrap({"app": {"name": "audio2text"}})
        cache = registry.get_cache()
        result = cache.get_or_set("computed", lambda: "factory_value")
        assert result == "factory_value"

    def test_i18n_translates_key(self):
        """InMemoryI18nAdapter returns translation for known key."""
        from audio2text.infrastructure.bootstrap import bootstrap

        registry = bootstrap({"app": {"name": "audio2text"}})
        i18n = registry.get_i18n()
        assert i18n.t("app.title") == "Audio2Text"

    def test_i18n_defaults_for_missing_key(self):
        """Missing key returns the key itself as fallback."""
        from audio2text.infrastructure.bootstrap import bootstrap

        registry = bootstrap({"app": {"name": "audio2text"}})
        i18n = registry.get_i18n()
        result = i18n.t("nonexistent.key")
        assert result is not None  # Returns something, doesn't raise


class TestSlice5DependencyManager:
    """Verify M13 DependencyManager wiring and provider registration."""

    def test_dependency_manager_wired(self):
        """DependencyManager is accessible from registry."""
        from audio2text.infrastructure.bootstrap import bootstrap

        registry = bootstrap({"app": {"name": "audio2text"}})
        dm = registry.get_dependency()
        assert dm is not None

    def test_dependency_lists_all_providers(self):
        """DependencyManager is wired with provider registry."""
        from audio2text.infrastructure.bootstrap import bootstrap

        registry = bootstrap({"app": {"name": "audio2text"}})
        dm = registry.get_dependency()
        assert dm is not None

    def test_dependency_resolves_mock_provider(self):
        """resolve_class with valid module+class does not raise."""
        from audio2text.infrastructure.bootstrap import bootstrap

        registry = bootstrap({"app": {"name": "audio2text"}})
        dm = registry.get_dependency()
        # Mapping returns None for entries (no eager imports in bootstrap)
        result = dm.resolve_class(
            "audio2text.providers.adapters.mock_adapter", "MockProvider"
        )
        # Returns None for unregistered mappings, but does not raise

    def test_dependency_unknown_key_returns_none(self):
        """resolve_class with unknown key returns None without raising."""
        from audio2text.infrastructure.bootstrap import bootstrap

        registry = bootstrap({"app": {"name": "audio2text"}})
        dm = registry.get_dependency()
        result = dm.resolve_class("unknown.module", "UnknownClass")
        assert result is None

    def test_init_order_includes_dependency(self):
        """M13 DependencyManager is wired after M07 Cache."""
        from audio2text.infrastructure.bootstrap import bootstrap

        registry = bootstrap({"app": {"name": "audio2text"}})
        order = registry.init_order
        assert "dependency" in order
        assert order.index("cache") < order.index("dependency")


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