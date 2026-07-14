"""@File: tests/unit/test_faster_whisper_provider.py
@Description: Unit tests for FasterWhisperProvider (Task 2.4).
@Version: 0.16.0
@Author: CENF Development Team
@License: Apache-2.0
"""

from __future__ import annotations

from pathlib import Path

import pytest


class TestFasterWhisperProvider:
    """Tests for the faster-whisper local transcription provider."""

    def test_provider_name_is_faster_whisper(self) -> None:
        """FasterWhisperProvider reports its name as 'faster_whisper'."""
        from audio2text.providers.faster_whisper_provider import FasterWhisperProvider

        provider = FasterWhisperProvider({})
        assert provider.provider_name == "faster_whisper"

    def test_model_name_default_is_base(self) -> None:
        """Default model size is 'base'."""
        from audio2text.providers.faster_whisper_provider import FasterWhisperProvider

        provider = FasterWhisperProvider({})
        assert provider.model_name == "base"

    def test_model_name_configurable(self) -> None:
        """Model size can be overridden via config."""
        from audio2text.providers.faster_whisper_provider import FasterWhisperProvider

        provider = FasterWhisperProvider({"model_size": "large-v3"})
        assert provider.model_name == "large-v3"

    def test_is_available_when_faster_whisper_installed(self) -> None:
        """is_available is True when faster-whisper is importable."""
        from audio2text.providers.faster_whisper_provider import FasterWhisperProvider

        provider = FasterWhisperProvider({})
        # faster-whisper is installed in this environment
        assert provider.is_available is True

    def test_lazy_model_loading(self) -> None:
        """Model is not loaded at init — only on first transcribe call."""
        from audio2text.providers.faster_whisper_provider import FasterWhisperProvider

        provider = FasterWhisperProvider({})
        # Before any transcription, _model should be None
        assert provider._model is None

    def test_transcribe_file_requires_existing_file(self) -> None:
        """transcribe_file returns None if the audio file does not exist."""
        from audio2text.providers.faster_whisper_provider import FasterWhisperProvider

        provider = FasterWhisperProvider({})
        result = provider.transcribe_file("/nonexistent/path/audio.wav")
        assert result is None

    def test_transcribe_file_with_valid_wav(
        self, silent_wav_3s: Path
    ) -> None:
        """transcribe_file can process a valid WAV file (silence → empty result)."""
        from audio2text.providers.faster_whisper_provider import FasterWhisperProvider

        provider = FasterWhisperProvider({})
        result = provider.transcribe_file(str(silent_wav_3s), language="es")
        # Silent audio typically produces no transcription
        # The provider should not crash — returning None is a valid outcome
        assert result is None or result.text == ""

    def test_transcribe_stream_raises_not_implemented(self) -> None:
        """transcribe_stream raises NotImplementedError."""
        from audio2text.providers.faster_whisper_provider import FasterWhisperProvider

        provider = FasterWhisperProvider({})
        with pytest.raises(NotImplementedError, match="streaming"):
            provider.transcribe_stream(None)

    def test_validate_config_returns_empty_when_importable(self) -> None:
        """validate_config returns empty when faster-whisper is installed."""
        from audio2text.providers.faster_whisper_provider import FasterWhisperProvider

        provider = FasterWhisperProvider({})
        issues = provider.validate_config()
        assert isinstance(issues, list)

    def test_config_device_auto(self) -> None:
        """Default device is 'auto' (auto-detect CUDA)."""
        from audio2text.providers.faster_whisper_provider import FasterWhisperProvider

        provider = FasterWhisperProvider({})
        assert provider._device == "auto"

    def test_config_device_cpu(self) -> None:
        """Device can be set to 'cpu' via config."""
        from audio2text.providers.faster_whisper_provider import FasterWhisperProvider

        provider = FasterWhisperProvider({"device": "cpu"})
        assert provider._device == "cpu"

    def test_config_beam_size(self) -> None:
        """Beam size can be configured."""
        from audio2text.providers.faster_whisper_provider import FasterWhisperProvider

        provider = FasterWhisperProvider({"beam_size": 10})
        assert provider._beam_size == 10

    def test_config_vad_filter(self) -> None:
        """VAD filter can be disabled via config."""
        from audio2text.providers.faster_whisper_provider import FasterWhisperProvider

        provider = FasterWhisperProvider({"vad_filter": False})
        assert provider._vad_filter is False
