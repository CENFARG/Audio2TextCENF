"""
Bootstrap orchestrator — wires core-cenf managers in dependency order.

Spec: "ConfigManager (M01) → LoggerManager (M02) → SecretManager (M03)
       → ErrorHandlingManager (M04) → ..."
Slice 5 adds M13 DependencyManager with provider registration.

Golden rule: only audio2text/infrastructure/ may import core_infrastructure.
"""

from __future__ import annotations

from typing import Any

from core_infrastructure.bus_event.adapters.memory_bus_adapter import MemoryBusAdapter
from core_infrastructure.cache import MemoryCacheAdapter
from core_infrastructure.common.errors import ValidationError
from core_infrastructure.config import InMemoryConfigAdapter
from core_infrastructure.dependency import InMemoryDependencyAdapter
from core_infrastructure.errors import CapturingErrorAdapter
from core_infrastructure.external_api import MockHTTPAdapter
from core_infrastructure.i18n import InMemoryI18nAdapter
from core_infrastructure.logger import InMemoryLoggerAdapter
from core_infrastructure.observability import NoopObservabilityAdapter
from core_infrastructure.secrets import InMemorySecretAdapter
from core_infrastructure.state_machine import InMemoryStateMachineAdapter, StateMachineConfig

from audio2text.infrastructure.registry import ManagerRegistry


def bootstrap(config_dict: dict[str, Any] | None) -> ManagerRegistry:
    """Wire managers in dependency order and return a populated registry.

    Order: M01 Config → M02 Logger → M03 Secrets → M04 Errors
       → M05 Observability → M07 Cache → M17 I18n.

    Args:
        config_dict: Configuration values to seed InMemoryConfigAdapter.
            Must not be None.

    Returns:
        ManagerRegistry with M01–M05, M07, M13, M17 wired.

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

    # M05: ObservabilityManager — depends on config + logger
    observability = NoopObservabilityAdapter()
    registry.register("observability", observability)

    # M07: CacheManager — depends on config + logger + errors
    cache = MemoryCacheAdapter(config=config, logger=logger, error_handler=errors)
    registry.register("cache", cache)

    # M13: DependencyManager — depends on config; registers provider adapters
    dependency = InMemoryDependencyAdapter(mapping={
        ("audio2text.providers.adapters.groq_adapter", "GroqProvider"): None,
        ("audio2text.providers.adapters.faster_whisper_adapter", "FasterWhisperProvider"): None,
        ("audio2text.providers.adapters.nvidia_riva_adapter", "NvidiaRivaProvider"): None,
        ("audio2text.providers.adapters.mock_adapter", "MockProvider"): None,
    })
    registry.register("dependency", dependency)

    # M11: ExternalAPIManager — depends on config; used for LLM/API calls
    external_api = MockHTTPAdapter()
    registry.register("external_api", external_api)

    # M21: BusEventManager — decoupled pub/sub for component events
    bus = MemoryBusAdapter(config=None)
    registry.register("bus", bus)

    # M22: StateMachineManager — deterministic FSM for recording lifecycle
    fsm_config = StateMachineConfig(initial_state="idle")
    fsm = InMemoryStateMachineAdapter(config=fsm_config)
    registry.register("fsm", fsm)

    # M17: I18nManager — depends on config
    i18n = InMemoryI18nAdapter(
        translations={"es_ES": {"app": {"title": "Audio2Text"}}, "en_US": {"app": {"title": "Audio2Text"}}},
        default_locale=config.get_string("app.language", "es_ES"),
        fallback_locale="en_US",
    )
    registry.register("i18n", i18n)

    return registry