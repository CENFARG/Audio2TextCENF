"""@File: audio2text/providers/factory.py
@Description: Transcription provider factory — creates providers by type identifier.
@Version: 0.16.0
@Author: CENF Development Team
@License: Apache-2.0
"""

from __future__ import annotations

import importlib
from collections.abc import Callable
from typing import Any

from audio2text.providers.ports import TranscriptionProvider


class TranscriptionProviderFactory:
    """Factory that creates TranscriptionProvider instances by type key.

    Delegates to DependencyManager (M13) for adapter resolution.
    Supported provider types: groq, faster_whisper, nvidia, mock.
    """

    # Maps provider type keys to import paths (lazy imports)
    _PROVIDER_REGISTRY: dict[str, str] = {
        "groq": "audio2text.providers.adapters.groq_adapter",
        "faster_whisper": "audio2text.providers.adapters.faster_whisper_adapter",
        "nvidia": "audio2text.providers.adapters.nvidia_riva_adapter",
        "mock": "audio2text.providers.adapters.mock_adapter",
    }

    # Maps provider type keys to class names within those modules
    _CLASS_REGISTRY: dict[str, str] = {
        "groq": "GroqProvider",
        "faster_whisper": "FasterWhisperProvider",
        "nvidia": "NvidiaRivaProvider",
        "mock": "MockProvider",
    }

    @classmethod
    def list_available(cls) -> list[str]:
        """List all known provider type identifiers.

        Returns:
            Sorted list of provider type keys.
        """
        return sorted(cls._PROVIDER_REGISTRY.keys())

    @classmethod
    def create(cls, provider_type: str, config: dict[str, Any]) -> TranscriptionProvider:
        """Create a transcription provider instance.

        Uses internal lazy-import registry. Future: delegate to DependencyManager (M13).
        """
        provider_type = provider_type.lower().strip()

        if provider_type not in cls._PROVIDER_REGISTRY:
            valid = ", ".join(cls.list_available())
            raise ValueError(
                f"Unknown provider: {provider_type!r}. Valid providers: {valid}"
            )

        module_path = cls._PROVIDER_REGISTRY[provider_type]
        class_name = cls._CLASS_REGISTRY[provider_type]

        module = importlib.import_module(module_path)
        provider_cls: Callable[..., TranscriptionProvider] = getattr(module, class_name)
        return provider_cls(config=config)

    @classmethod
    def get_default(cls) -> TranscriptionProvider:
        """Return the first available provider, or MockProvider as fallback.

        Checks providers in order: groq → faster_whisper → nvidia → mock.
        MockProvider is always available, so this method never raises.

        Returns:
            A TranscriptionProvider instance that is ready to use.
        """
        for ptype in ("groq", "faster_whisper", "nvidia", "mock"):
            try:
                provider = cls.create(ptype, {})
                if provider.is_available:
                    return provider
            except Exception:
                continue

        # Ultimate fallback — mock is always available
        return cls.create("mock", {})
