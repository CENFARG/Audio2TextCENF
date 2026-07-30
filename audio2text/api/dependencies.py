"""@File: audio2text/api/dependencies.py
@Description: FastAPI dependency injection — uses ManagerRegistry from bootstrap.
    All services are resolved from the bootstrapped registry instead of
    direct imports. Single import site for core_infrastructure via infrastructure/.
@Version: 0.16.0
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
    """Return a TranscriptionProvider from factory (delegates to DependencyManager M13)."""
    from audio2text.providers.factory import TranscriptionProviderFactory

    config = get_config()
    primary = config.get_string("providers.primary", "mock")
    return TranscriptionProviderFactory.create(primary, {})


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
    return None


def get_vocabulary_service():
    return None


def get_block_processor():
    return None