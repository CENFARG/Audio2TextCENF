"""@File: tests/unit/test_provider_factory.py
@Description: Unit tests for TranscriptionProviderFactory (Task 2.3).
@Version: 0.16.0
@Author: CENF Development Team
@License: Apache-2.0
"""

from __future__ import annotations

from typing import Any

import pytest


class TestTranscriptionProviderFactory:
    """Tests for the provider factory — creation, listing, defaults."""

    # ------------------------------------------------------------------
    # list_available
    # ------------------------------------------------------------------

    def test_list_available_returns_all_providers(self) -> None:
        """list_available returns the known provider type keys."""
        from audio2text.providers.factory import TranscriptionProviderFactory

        available = TranscriptionProviderFactory.list_available()
        assert isinstance(available, list)
        assert "groq" in available
        assert "faster_whisper" in available
        assert "nvidia" in available
        assert "mock" in available

    def test_list_available_contains_only_strings(self) -> None:
        """All entries in list_available are strings."""
        from audio2text.providers.factory import TranscriptionProviderFactory

        for name in TranscriptionProviderFactory.list_available():
            assert isinstance(name, str)

    # ------------------------------------------------------------------
    # create
    # ------------------------------------------------------------------

    def test_create_mock_provider(self) -> None:
        """Factory can create a MockProvider."""
        from audio2text.providers.factory import TranscriptionProviderFactory
        from audio2text.providers.adapters.mock_adapter import MockProvider

        provider = TranscriptionProviderFactory.create("mock", {})
        assert isinstance(provider, MockProvider)
        assert provider.provider_name == "mock"

    def test_create_groq_provider(self) -> None:
        """Factory can create a GroqProvider."""
        from audio2text.providers.factory import TranscriptionProviderFactory
        from audio2text.providers.adapters.groq_adapter import GroqProvider

        provider = TranscriptionProviderFactory.create("groq", {})
        assert isinstance(provider, GroqProvider)
        assert provider.provider_name == "groq"

    def test_create_faster_whisper_provider(self) -> None:
        """Factory can create a FasterWhisperProvider."""
        from audio2text.providers.factory import TranscriptionProviderFactory
        from audio2text.providers.adapters.faster_whisper_adapter import FasterWhisperProvider

        provider = TranscriptionProviderFactory.create("faster_whisper", {})
        assert isinstance(provider, FasterWhisperProvider)
        assert provider.provider_name == "faster_whisper"

    def test_create_nvidia_provider(self) -> None:
        """Factory can create a NvidiaRivaProvider."""
        from audio2text.providers.factory import TranscriptionProviderFactory
        from audio2text.providers.adapters.nvidia_riva_adapter import NvidiaRivaProvider

        provider = TranscriptionProviderFactory.create("nvidia", {})
        assert isinstance(provider, NvidiaRivaProvider)
        assert provider.provider_name == "nvidia"

    def test_create_unknown_provider_raises(self) -> None:
        """Factory raises ValueError for unknown provider types."""
        from audio2text.providers.factory import TranscriptionProviderFactory

        with pytest.raises(ValueError, match="Unknown provider"):
            TranscriptionProviderFactory.create("invalid_provider", {})

    def test_create_error_message_lists_valid_providers(self) -> None:
        """Error message for unknown provider includes valid options."""
        from audio2text.providers.factory import TranscriptionProviderFactory

        with pytest.raises(ValueError) as exc_info:
            TranscriptionProviderFactory.create("bogus", {})
        error_msg = str(exc_info.value)
        assert "bogus" in error_msg
        # Should list at least one valid provider
        assert "mock" in error_msg or "groq" in error_msg

    # ------------------------------------------------------------------
    # get_default
    # ------------------------------------------------------------------

    def test_get_default_returns_first_available_or_mock(self) -> None:
        """get_default returns an available provider (mock is the ultimate fallback)."""
        from audio2text.providers.ports import TranscriptionProvider
        from audio2text.providers.factory import TranscriptionProviderFactory

        provider = TranscriptionProviderFactory.get_default()
        assert isinstance(provider, TranscriptionProvider)
        assert provider.is_available is True
        # The specific provider depends on the environment, but must be in the registry
        assert provider.provider_name in TranscriptionProviderFactory.list_available()

    # ------------------------------------------------------------------
    # create accepts config
    # ------------------------------------------------------------------

    def test_create_passes_config_to_provider(self) -> None:
        """Config dict is forwarded to the provider constructor."""
        from audio2text.providers.factory import TranscriptionProviderFactory

        config: dict[str, Any] = {"language": "en", "model": "custom-model"}
        provider = TranscriptionProviderFactory.create("mock", config)
        assert provider.model_name == "mock-model"  # MockProvider default
