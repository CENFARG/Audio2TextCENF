"""
Tests for TranscriptionProvider Protocol — structural duck-typing.
"""

import pytest


class TestTranscriptionProviderProtocol:
    """Verify Protocol works with duck-typing (no inheritance needed)."""

    def test_mock_provider_satisfies_protocol(self):
        """MockProvider satisfies Protocol via duck-typing."""
        from audio2text.providers.ports import TranscriptionProvider
        from audio2text.providers.adapters import MockProvider

        provider = MockProvider()
        assert isinstance(provider, TranscriptionProvider)

    def test_groq_provider_does_not_satisfy_without_import(self):
        """GroqProvider adapter module exists and is importable."""
        from audio2text.providers.adapters import GroqProvider

        provider = GroqProvider(config={})
        assert provider.provider_name == "groq"
        assert isinstance(provider.model_name, str)

    def test_all_adapters_importable(self):
        """All 4 adapters can be imported from adapters package."""
        from audio2text.providers.adapters import (
            GroqProvider,
            FasterWhisperProvider,
            NvidiaRivaProvider,
            MockProvider,
        )

        assert GroqProvider(config={}).provider_name == "groq"
        assert FasterWhisperProvider(config={}).provider_name == "faster_whisper"
        assert NvidiaRivaProvider(config={}).provider_name == "nvidia"
        assert MockProvider(config={}).provider_name == "mock"

    def test_factory_creates_protocol_compatible_providers(self):
        """Factory-created providers satisfy the Protocol."""
        from audio2text.providers.ports import TranscriptionProvider
        from audio2text.providers.factory import TranscriptionProviderFactory

        for ptype in ("groq", "faster_whisper", "nvidia", "mock"):
            provider = TranscriptionProviderFactory.create(ptype, {})
            assert isinstance(provider, TranscriptionProvider), (
                f"{ptype} provider does not satisfy Protocol"
            )
