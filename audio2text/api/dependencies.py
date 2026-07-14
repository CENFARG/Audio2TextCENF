"""@File: audio2text/api/dependencies.py
@Description: FastAPI dependency injection providers for all services.
    Uses cenf-core ConfigManager + SecretManager. Creates real provider
    instances based on config, wires the pipeline with defaults, and
    injects LocalizationManager where needed.
@Version: 0.16.0
@Author: CENF Development Team
@License: Apache-2.0
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

from cenf_core import ConfigManager, SecretManager

from audio2text.config.schema import Audio2TextConfig
from audio2text.localization.manager import LocalizationManager

if TYPE_CHECKING:
    from audio2text.providers.base import TranscriptionProvider as _TranscriptionProvider
    from audio2text.services.ai_enhancement_service import AIEnhancementService
    from audio2text.services.block_loader_service import BlockLoaderService
    from audio2text.services.block_processing_service import BlockProcessingService
    from audio2text.services.metadata_service import MetadataService
    from audio2text.services.transcription_service import TranscriptionService
    from audio2text.services.vocabulary_service import VocabularyService

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Singleton cache — services that should live for the app lifetime.
# ---------------------------------------------------------------------------

_config_manager: ConfigManager[Audio2TextConfig] | None = None
_secret_manager: SecretManager | None = None
_localization: LocalizationManager | None = None
_metadata_service: MetadataService | None = None
_vocabulary_service: VocabularyService | None = None
_block_loader: BlockLoaderService | None = None
_block_processor: BlockProcessingService | None = None
_ai_enhancement: AIEnhancementService | None = None


# ---------------------------------------------------------------------------
# Core infrastructure
# ---------------------------------------------------------------------------

def get_config() -> ConfigManager[Audio2TextConfig]:
    """Return a singleton ConfigManager with Audio2Text v0.16 schema."""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager(
            schema_class=Audio2TextConfig,
            env_prefix="A2T_",
        )
        # Load config file if it exists
        config_path = Path("config/config.json")
        if config_path.exists():
            try:
                _config_manager.load_file(config_path)
            except Exception as exc:
                logger.warning("Could not load config file: %s", exc)
        _config_manager.load_env()
    return _config_manager


def get_secrets() -> SecretManager:
    """Return a singleton SecretManager for API keys."""
    global _secret_manager
    if _secret_manager is None:
        _secret_manager = SecretManager(
            service_name="audio2text",
            env_prefix="A2T_SECRET_",
        )
    return _secret_manager


def get_localization() -> LocalizationManager:
    """Return a singleton LocalizationManager."""
    global _localization
    if _localization is None:
        config = get_config()
        lang = config.get("localization.language", "es_ES")
        fallback = config.get("localization.fallback", "en_US")
        locales_dir = config.get("localization.locales_dir", "./audio2text/locales")
        _localization = LocalizationManager(
            language=lang,
            fallback_language=fallback,
            locales_dir=Path(locales_dir),
        )
    return _localization


# ---------------------------------------------------------------------------
# Metadata
# ---------------------------------------------------------------------------

def get_metadata_service(storage_dir: str | None = None) -> MetadataService:
    """Return a singleton MetadataService instance."""
    from audio2text.services.metadata_service import MetadataService

    global _metadata_service
    if _metadata_service is None:
        default_dir = storage_dir or "transcriptions"
        try:
            config = get_config()
            default_dir = config.get("audio.recordings_dir", default_dir)
        except Exception:
            pass
        _metadata_service = MetadataService(storage_dir=default_dir)
    return _metadata_service


# ---------------------------------------------------------------------------
# Vocabulary
# ---------------------------------------------------------------------------

def get_vocabulary_service() -> VocabularyService:
    """Return a singleton VocabularyService loaded from configured paths."""
    from audio2text.domain.vocabulary import VocabularyConfig
    from audio2text.services.vocabulary_service import VocabularyService

    global _vocabulary_service
    if _vocabulary_service is None:
        vocab_config = VocabularyConfig()
        # Load vocabulary from configured paths if available
        try:
            config = get_config()
            custom_path = config.get("vocabulary.custom_path")
            if custom_path:
                from audio2text.api._vocab_loader import load_vocab_from_path
                load_vocab_from_path(vocab_config, Path(custom_path))
        except Exception:
            pass
        _vocabulary_service = VocabularyService(config=vocab_config)
    return _vocabulary_service


# ---------------------------------------------------------------------------
# Block Loader
# ---------------------------------------------------------------------------

def get_block_loader(blocks_dir: str | None = None) -> BlockLoaderService:
    """Return a singleton BlockLoaderService with configurable blocks dir."""
    from audio2text.services.block_loader_service import BlockLoaderService

    global _block_loader
    if _block_loader is None:
        default_dir = blocks_dir or "."
        try:
            config = get_config()
            default_dir = config.get("context_blocks.directory", default_dir)
        except Exception:
            pass
        _block_loader = BlockLoaderService(blocks_dir=default_dir)
    return _block_loader


# ---------------------------------------------------------------------------
# Block Processor
# ---------------------------------------------------------------------------

def get_block_processor() -> BlockProcessingService:
    """Return a singleton BlockProcessingService instance."""
    from audio2text.services.block_processing_service import BlockProcessingService

    global _block_processor
    if _block_processor is None:
        _block_processor = BlockProcessingService()
    return _block_processor


# ---------------------------------------------------------------------------
# AI Enhancement
# ---------------------------------------------------------------------------

def get_ai_enhancement() -> AIEnhancementService:
    """Return a singleton AIEnhancementService with locale-aware prompts."""
    from audio2text.services.ai_enhancement_service import AIEnhancementService

    global _ai_enhancement
    if _ai_enhancement is None:
        secrets = get_secrets()
        config = get_config()

        # Try to get API key from secrets manager
        api_key: str | None = None
        try:
            secret_key_name = config.get("providers.groq.api_key_secret_key", "groq_api_key")
            api_key = secrets.get(secret_key_name)
        except Exception:
            pass

        model = config.get("ai_enhancement.groq_model", "llama-3.3-70b-versatile")
        locale = get_localization()

        _ai_enhancement = AIEnhancementService(
            api_key=api_key,
            model=model,
            locale_manager=locale,
        )
    return _ai_enhancement


# ---------------------------------------------------------------------------
# Provider
# ---------------------------------------------------------------------------

def get_provider() -> _TranscriptionProvider:
    """Return a TranscriptionProvider based on the configured primary provider.

    Resolves the provider type from config, fetches the API key from
    SecretManager, and returns the appropriate provider instance.
    Falls back to MockProvider if the real provider is unavailable.
    """
    from audio2text.providers.base import TranscriptionProvider
    from audio2text.providers.mock_provider import MockProvider

    config = get_config()
    secrets = get_secrets()

    primary = config.get("providers.primary", "mock")

    if primary == "groq":
        try:
            from audio2text.providers.groq_provider import GroqProvider
            secret_key = config.get("providers.groq.api_key_secret_key", "groq_api_key")
            api_key = secrets.get(secret_key) or ""
            model = config.get("providers.groq.model", "whisper-large-v3")
            return GroqProvider(config={
                "api_key": api_key,
                "model": model,
            })
        except Exception as exc:
            logger.warning("Groq provider unavailable: %s — falling back to Mock.", exc)

    if primary == "faster_whisper":
        try:
            from audio2text.providers.faster_whisper_provider import FasterWhisperProvider
            model_size = config.get("providers.faster_whisper.model_size", "base")
            device = config.get("providers.faster_whisper.device", "auto")
            return FasterWhisperProvider(config={
                "model_size": model_size,
                "device": device,
            })
        except Exception as exc:
            logger.warning("FasterWhisper provider unavailable: %s — falling back to Mock.", exc)

    if primary == "nvidia":
        try:
            from audio2text.providers.nvidia_riva_provider import NvidiaRivaProvider
            secret_key = config.get("providers.nvidia_riva.api_key_secret_key", "nvidia_api_key")
            api_key = secrets.get(secret_key) or ""
            return NvidiaRivaProvider(config={"api_key": api_key})
        except Exception as exc:
            logger.warning("NvidiaRiva provider unavailable: %s — falling back to Mock.", exc)

    provider: TranscriptionProvider = MockProvider()
    return provider


# ---------------------------------------------------------------------------
# Transcription Service
# ---------------------------------------------------------------------------

def get_transcription_service() -> TranscriptionService | None:
    """Return a singleton TranscriptionService with wired pipeline stages."""
    from audio2text.pipeline.pipeline import TranscriptionPipeline
    from audio2text.services.transcription_service import TranscriptionService

    global _metadata_service

    try:
        provider = get_provider()
        pipeline = TranscriptionPipeline()
        metadata = get_metadata_service()

        # Wire default pipeline stages from real services
        vocab_svc = get_vocabulary_service()
        block_svc = get_block_processor()
        ai_svc = get_ai_enhancement()

        pipeline.with_defaults(
            vocab_service=vocab_svc,
            block_service=block_svc,
            ai_service=ai_svc,
        )

        return TranscriptionService(
            provider=provider,
            pipeline=pipeline,
            metadata_service=metadata,
        )
    except Exception as exc:
        logger.error("Failed to create TranscriptionService: %s", exc)
        return None
