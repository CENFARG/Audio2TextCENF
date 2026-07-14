"""@File: tests/unit/test_mock_provider.py
@Description: Unit tests for MockProvider (Task 2.5).
@Version: 0.16.0
@Author: CENF Development Team
@License: Apache-2.0
"""

from __future__ import annotations


class TestMockProvider:
    """Tests for the Mock transcription provider (always available, test-friendly)."""

    def test_provider_name_is_mock(self) -> None:
        """MockProvider reports its name as 'mock'."""
        from audio2text.providers.mock_provider import MockProvider

        provider = MockProvider({})
        assert provider.provider_name == "mock"

    def test_model_name_is_mock_model(self) -> None:
        """MockProvider model name is 'mock-model'."""
        from audio2text.providers.mock_provider import MockProvider

        provider = MockProvider({})
        assert provider.model_name == "mock-model"

    def test_is_available_always_true(self) -> None:
        """MockProvider is always available."""
        from audio2text.providers.mock_provider import MockProvider

        provider = MockProvider({})
        assert provider.is_available is True

    def test_validate_config_always_empty(self) -> None:
        """MockProvider configuration is always valid."""
        from audio2text.providers.mock_provider import MockProvider

        provider = MockProvider({})
        assert provider.validate_config() == []

    def test_transcribe_file_returns_default_result(self) -> None:
        """transcribe_file returns a canned TranscriptionResult."""
        from audio2text.providers.mock_provider import MockProvider

        provider = MockProvider({})
        result = provider.transcribe_file("any.wav")
        assert result is not None
        assert result.text == "Mock transcription result"
        assert result.language == "es"
        assert result.confidence == 0.99
        assert result.provider_name == "mock"
        assert result.model_name == "mock-model"

    def test_transcribe_file_respects_custom_text(self) -> None:
        """Canned text can be customized via config."""
        from audio2text.providers.mock_provider import MockProvider

        provider = MockProvider({"text": "Hola mundo desde mock"})
        result = provider.transcribe_file("any.wav")
        assert result is not None
        assert result.text == "Hola mundo desde mock"

    def test_transcribe_file_respects_custom_language(self) -> None:
        """Canned language can be customized via config."""
        from audio2text.providers.mock_provider import MockProvider

        provider = MockProvider({"language": "en"})
        result = provider.transcribe_file("any.wav")
        assert result is not None
        assert result.language == "en"

    def test_transcribe_file_respects_custom_confidence(self) -> None:
        """Confidence can be customized via config."""
        from audio2text.providers.mock_provider import MockProvider

        provider = MockProvider({"confidence": 0.5})
        result = provider.transcribe_file("any.wav")
        assert result is not None
        assert result.confidence == 0.5

    def test_transcribe_file_passes_language_parameter(self) -> None:
        """Language parameter passed to transcribe_file overrides config."""
        from audio2text.providers.mock_provider import MockProvider

        provider = MockProvider({"language": "es"})
        result = provider.transcribe_file("any.wav", language="en")
        assert result is not None
        assert result.language == "en"

    def test_transcribe_stream_returns_same_as_file(self) -> None:
        """transcribe_stream returns same format as transcribe_file."""
        from audio2text.providers.mock_provider import MockProvider

        provider = MockProvider({"text": "stream result"})
        result = provider.transcribe_stream(None)
        assert result is not None
        assert result.text == "stream result"
        assert result.provider_name == "mock"

    def test_error_after_n_calls(self) -> None:
        """When error_after is set, transcribe fails after N successful calls."""
        from audio2text.providers.mock_provider import MockProvider

        provider = MockProvider({"error_after": 2})
        # Calls 1 and 2 succeed
        r1 = provider.transcribe_file("a.wav")
        assert r1 is not None
        r2 = provider.transcribe_file("b.wav")
        assert r2 is not None
        # Call 3 fails (error_after=2, so >2 fails)
        r3 = provider.transcribe_file("c.wav")
        assert r3 is None

    def test_error_after_only_affects_file_transcription(self) -> None:
        """error_after applies to transcribe_file; transcribe_stream resets."""
        from audio2text.providers.mock_provider import MockProvider

        provider = MockProvider({"error_after": 1})
        # First call succeeds
        r1 = provider.transcribe_file("a.wav")
        assert r1 is not None
        # Second call fails (call_count = 2 > error_after = 1)
        r2 = provider.transcribe_file("b.wav")
        assert r2 is None

    def test_default_error_after_is_none(self) -> None:
        """By default, error_after is None — unlimited successful calls."""
        from audio2text.providers.mock_provider import MockProvider

        provider = MockProvider({})
        for _ in range(10):
            result = provider.transcribe_file("any.wav")
            assert result is not None
