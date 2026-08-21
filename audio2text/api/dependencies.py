"""@File: audio2text/api/dependencies.py
@Description: FastAPI dependency injection — uses ManagerRegistry from bootstrap.
    All services are resolved from the bootstrapped registry instead of
    direct imports. Single import site for core_infrastructure via infrastructure/.
@Version: 0.17.0
@Author: CENF Development Team
@License: Apache-2.0
"""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING

from audio2text.infrastructure import get_registry
from audio2text.localization.manager import LocalizationManager

if TYPE_CHECKING:
    from audio2text.services.transcription_service import TranscriptionService

logger = logging.getLogger(__name__)


def get_config():
    """Return ConfigManager (M01) from bootstrapped registry."""
    return get_registry().get_config()


def get_secrets():
    """Return SecretManager (M03) from bootstrapped registry."""
    return get_registry().get_secrets()


def get_logger():
    """Return LoggerManager (M02) from bootstrapped registry."""
    return get_registry().get_logger()


def get_errors():
    """Return ErrorHandlingManager (M04) from bootstrapped registry."""
    return get_registry().get_errors()


def get_cache():
    """Return CacheManager (M07) from bootstrapped registry."""
    return get_registry().get_cache()


def get_i18n():
    """Return I18nManager (M17) from bootstrapped registry."""
    return get_registry().get_i18n()


def get_localization():
    """Return a LocalizationManager backed by registry I18nManager."""
    i18n = get_i18n()
    config = get_config()
    lang = config.get_string("localization.language", "es_ES")
    return LocalizationManager(language=lang)


def get_provider():
    """Return a TranscriptionProvider from factory (delegates to DependencyManager M13).

    Single Owner: if primary provider is not available, fallback to mock
    so offline/mock always works (mock sin conexión).
    """
    from audio2text.providers.factory import TranscriptionProviderFactory

    config = get_config()
    try:
        primary = config.get_string("providers.primary", "groq")
    except Exception:
        primary = "groq"

    try:
        provider = TranscriptionProviderFactory.create(primary, {})
    except Exception as exc:
        logger.warning("Failed to create provider %s: %s, falling back to mock", primary, exc)
        try:
            provider = TranscriptionProviderFactory.create("mock", {})
        except Exception:
            from audio2text.providers.adapters.mock_adapter import MockProvider

            return MockProvider({})

    # If primary is not mock and provider is not available, fallback to mock
    try:
        if not getattr(provider, "is_available", True) and primary != "mock":
            logger.warning("Provider %s not available, falling back to mock", primary)
            provider = TranscriptionProviderFactory.create("mock", {})
    except Exception as exc:
        logger.warning("Fallback to mock failed: %s", exc)
        try:
            provider = TranscriptionProviderFactory.create("mock", {})
        except Exception:
            from audio2text.providers.adapters.mock_adapter import MockProvider

            return MockProvider({})

    return provider


def get_transcription_service():
    """Return TranscriptionService with registry-injected dependencies."""
    from audio2text.pipeline.pipeline import TranscriptionPipeline
    from audio2text.services.transcription_service import TranscriptionService

    try:
        provider = get_provider()
        pipeline = TranscriptionPipeline()
        return TranscriptionService(
            provider=provider,
            pipeline=pipeline,
            metadata_service=None,  # TODO: wire MetadataService from registry
        )
    except Exception as exc:
        logger.error("Failed to create TranscriptionService: %s", exc)
        return None


# ── Stubs for routes not yet migrated to registry ─────────────────────────

def get_ai_enhancement():
    return None


def get_metadata_service():
    from audio2text.services.metadata_service import MetadataService

    return MetadataService()


def get_vocabulary_service():
    return None


def get_block_processor():
    return None
