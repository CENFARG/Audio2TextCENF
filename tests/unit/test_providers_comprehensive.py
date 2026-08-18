"""Tests for audio2text.providers — comprehensive provider coverage."""

from __future__ import annotations

import pytest

from audio2text.providers.ports import TranscriptionProvider
from audio2text.providers.factory import TranscriptionProviderFactory
from audio2text.providers.adapters.mock_adapter import MockProvider
from audio2text.domain.transcription import TranscriptionResult


class TestTranscriptionProviderProtocol:
    """Tests for TranscriptionProvider protocol compliance."""

    def test_mock_satisfies_protocol(self):
        """MockProvider should satisfy TranscriptionProvider protocol."""
        provider = MockProvider()
        assert isinstance(provider, TranscriptionProvider)

    def test_protocol_has_required_methods(self):
        """Protocol should define required methods."""
        assert hasattr(TranscriptionProvider, "transcribe_file")
        assert hasattr(TranscriptionProvider, "transcribe_stream")
        assert hasattr(TranscriptionProvider, "is_available")
        assert hasattr(TranscriptionProvider, "provider_name")
        assert hasattr(TranscriptionProvider, "model_name")
        assert hasattr(TranscriptionProvider, "validate_config")


class TestMockProvider:
    """Tests for MockProvider."""

    def test_always_available(self):
        """MockProvider should always be available."""
        provider = MockProvider()
        assert provider.is_available is True

    def test_default_transcription(self):
        """Should return default mock text."""
        provider = MockProvider()
        result = provider.transcribe_file("test.wav")
        assert result is not None
        assert result.text == "Mock transcription result"

    def test_custom_text(self):
        """Should use custom text from config."""
        provider = MockProvider(config={"text": "Custom text"})
        result = provider.transcribe_file("test.wav")
        assert result.text == "Custom text"

    def test_error_after(self):
        """Should return None after error_after calls."""
        provider = MockProvider(config={"error_after": 2})
        assert provider.transcribe_file("test.wav") is not None
        assert provider.transcribe_file("test.wav") is not None
        assert provider.transcribe_file("test.wav") is None

    def test_provider_name(self):
        """Provider name should be 'mock'."""
        provider = MockProvider()
        assert provider.provider_name == "mock"

    def test_model_name(self):
        """Model name should be 'mock-model'."""
        provider = MockProvider()
        assert provider.model_name == "mock-model"

    def test_validate_config_always_valid(self):
        """Validation should always pass."""
        provider = MockProvider()
        assert provider.validate_config() == []

    def test_language_override(self):
        """Should accept language parameter."""
        provider = MockProvider()
        result = provider.transcribe_file("test.wav", language="en")
        assert result.language == "en"


class TestTranscriptionProviderFactory:
    """Tests for TranscriptionProviderFactory."""

    def test_list_available(self):
        """Should list all known providers."""
        available = TranscriptionProviderFactory.list_available()
        assert "groq" in available
        assert "mock" in available
        assert "faster_whisper" in available
        assert "nvidia" in available

    def test_create_mock(self):
        """Should create MockProvider."""
        provider = TranscriptionProviderFactory.create("mock", {})
        assert isinstance(provider, MockProvider)
        assert provider.is_available

    def test_create_unknown_raises(self):
        """Should raise ValueError for unknown provider."""
        with pytest.raises(ValueError, match="Unknown provider"):
            TranscriptionProviderFactory.create("nonexistent", {})

    def test_get_default_returns_available(self):
        """get_default should return an available provider."""
        provider = TranscriptionProviderFactory.get_default()
        assert provider.is_available

    def test_create_case_insensitive(self):
        """Should accept provider type in any case."""
        provider = TranscriptionProviderFactory.create("MOCK", {})
        assert isinstance(provider, MockProvider)


class TestTranscriptionResult:
    """Tests for TranscriptionResult domain model."""

    def test_creation(self):
        """Should create with required fields."""
        result = TranscriptionResult(
            text="Hello world",
            duration_seconds=5.0,
            language="es",
            provider_name="mock",
            model_name="mock-model",
        )
        assert result.text == "Hello world"
        assert result.duration_seconds == 5.0

    def test_optional_fields(self):
        """Should accept optional fields."""
        result = TranscriptionResult(
            text="Hello",
            duration_seconds=1.0,
            language="es",
            provider_name="mock",
            model_name="mock",
            confidence=0.95,
            segments=[],
        )
        assert result.confidence == 0.95
        assert result.segments == []
