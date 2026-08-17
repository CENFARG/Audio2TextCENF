"""
Unit tests for Transcriber class.

This module tests the core transcription functionality including:
- Initialization and configuration
- Recording management
- Transcription services (Groq, NVIDIA, faster-whisper)
- Block processing
- UTF-8 validation
- Hotkey handling

Author: Audio2Text Development Team
Version: 0.13.0
"""

import pytest
import sys
import os
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch, call
import numpy as np
import tempfile

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.transcriber import Transcriber, MIN_AUDIO_DURATION


@pytest.mark.unit
class TestTranscriberInitialization:
    """Tests for Transcriber initialization."""

    @pytest.fixture
    def mock_dependencies(self):
        """Create mock dependencies for Transcriber initialization."""
        config_manager = Mock()
        config_manager.get.side_effect = lambda key, default=None: {
            "hotkey": "F5",
            "record_mode": "toggle",
            "service": "groq",
            "language": "es",
            "model": "whisper-large-v3",
            "api_key": "test_key",
            "audio_priority_apps": [],
            "utf8_validation": True,
            "blocks": {},
        }.get(key, default)

        sound_manager = Mock()
        file_manager = Mock()
        update_status = Mock()
        transcription_callback = Mock()
        localization_manager = Mock()
        overlay_callback = Mock()

        return {
            "config_manager": config_manager,
            "sound_manager": sound_manager,
            "file_manager": file_manager,
            "update_status_callback": update_status,
            "transcription_callback": transcription_callback,
            "localization_manager": localization_manager,
            "overlay_callback": overlay_callback,
        }

    def test_initialization(self, mock_dependencies):
        """Test Transcriber initialization with all dependencies."""
        with patch("backend.transcriber.Groq"):
            transcriber = Transcriber(**mock_dependencies)

            assert transcriber.is_recording == False
            assert transcriber.hotkey == "F5"
            assert transcriber.record_mode == "toggle"
            assert transcriber.freq == 16000
            assert transcriber.audio_data == []
            assert transcriber.utf8_validation_enabled == True
            assert transcriber.block_manager is not None
            assert transcriber.custom_vocab is not None

    def test_initialization_with_overlay_callback(self, mock_dependencies):
        """Test that overlay callback is properly stored."""
        mock_dependencies["overlay_callback"] = Mock()
        with patch("backend.transcriber.Groq"):
            transcriber = Transcriber(**mock_dependencies)
            assert transcriber.overlay_callback == mock_dependencies["overlay_callback"]

    def test_hotkey_thread_started(self, mock_dependencies):
        """Test that hotkey listener thread is started on initialization."""
        with patch("backend.transcriber.Groq"):
            transcriber = Transcriber(**mock_dependencies)
            assert transcriber.hotkey_thread is not None
            assert transcriber.hotkey_thread.is_alive()


# Tests de grabación eliminados (v0.13.0) — reemplazados por test_captura_audio.py (v0.15.x)
# que testea el hot-loop de captura, cola de eventos, drenado y consistencia display/JSONL.
# Los mocks viejos no simulaban el contrato de sounddevice (read() retorna tupla)
# ni el nuevo flujo de cola de eventos.


@pytest.mark.unit
class TestTranscriptionServices:
    """Tests for transcription service integrations."""

    @pytest.fixture
    def transcriber(self, mock_dependencies):
        """Create a Transcriber instance."""
        with patch("backend.transcriber.Groq"):
            return Transcriber(**mock_dependencies)

    @pytest.fixture
    def mock_dependencies(self):
        """Create mock dependencies."""
        config_manager = Mock()
        config_manager.get.side_effect = lambda key, default=None: {
            "hotkey": "F5",
            "record_mode": "toggle",
            "service": "groq",
            "language": "es",
            "model": "whisper-large-v3",
            "api_key": "test_key",
            "audio_priority_apps": [],
            "utf8_validation": True,
            "blocks": {},
        }.get(key, default)

        return {
            "config_manager": config_manager,
            "sound_manager": Mock(),
            "file_manager": Mock(),
            "update_status_callback": Mock(),
            "transcription_callback": Mock(),
            "localization_manager": Mock(),
            "overlay_callback": Mock(),
        }

    @pytest.fixture
    def temp_audio_file(self):
        """Create a temporary audio file."""
        import wave

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            audio_path = f.name

        # Create WAV file
        with wave.open(audio_path, "wb") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(16000)
            silence = b"\x00\x00" * 16000
            wav_file.writeframes(silence)

        yield audio_path

        # Cleanup
        if os.path.exists(audio_path):
            os.unlink(audio_path)

    def test_transcribe_with_groq_success(self, transcriber, temp_audio_file):
        """Test successful transcription with Groq service."""
        # Mock Groq client — response_format="text" retorna string directo
        transcriber.cliente.audio.transcriptions.create = Mock(return_value="Texto de prueba")

        result = transcriber.transcribe_with_groq(temp_audio_file)

        assert result == "Texto de prueba"

    def test_transcribe_with_groq_error(self, transcriber, temp_audio_file):
        """Test Groq transcription error handling."""
        transcriber.cliente.audio.transcriptions.create = Mock(side_effect=Exception("API Error"))

        result = transcriber.transcribe_with_groq(temp_audio_file)

        assert result is None

    def test_get_transcription_service(self, transcriber):
        """Test getting current transcription service."""
        # Test Groq service
        transcriber.config_manager.get = Mock(return_value="groq")
        service = transcriber.get_transcription_service()
        assert service == "groq"

        # FIX: faster-whisper ERRADICADO — con asr_provider desconocido cae a Groq
        transcriber.config_manager.get = Mock(return_value="faster_whisper")
        service = transcriber.get_transcription_service()
        assert service == "groq"


# TestTextValidation eliminado (v0.13.0) — validate_text retorna (bool, list[str]),
# no (bool, str). Los tests asumían interfaz antigua. La validación UTF-8 se testea
# en test_captura_audio.py (test_display_y_jsonl_reciben_mismo_texto).


# TestBlockProcessing eliminado (v0.13.0) — block_manager es objeto real, no Mock.
# Los tests asignaban mocks a atributos de un objeto real. La funcionalidad de
# bloques se testea en los tests de integración.


# TestHotkeyManagement — se mantiene (test_update_hotkey)


# TestUTF8Validation eliminado (v0.13.0) — utf8_validator es objeto real, no Mock.
# Los tests hacían .assert_called_once() en métodos reales. La funcionalidad UTF-8
# se testea en test_captura_audio.py.


# TestBlockManagement eliminado (v0.13.0) — block_manager es objeto real, no Mock.
# Los tests hacían .assert_called_with() en métodos reales. enable_block/disable_block
# se testean en tests de integración.
    """Tests for hotkey management."""

    @pytest.fixture
    def transcriber(self):
        """Create a Transcriber instance."""
        config_manager = Mock()
        config_manager.get = Mock(
            side_effect=lambda k, d=None: {
                "hotkey": "F5",
                "record_mode": "toggle",
                "api_key": "test",
                "audio_priority_apps": [],
                "utf8_validation": True,
                "blocks": {},
            }.get(k, d)
        )

        mock_deps = {
            "config_manager": config_manager,
            "sound_manager": Mock(),
            "file_manager": Mock(),
            "update_status_callback": Mock(),
            "transcription_callback": Mock(),
            "localization_manager": Mock(),
            "overlay_callback": Mock(),
        }
        with patch("backend.transcriber.Groq"):
            return Transcriber(**mock_deps)

    def test_update_hotkey(self, transcriber):
        """Test updating hotkey configuration."""
        new_hotkey = "F10"
        transcriber.update_hotkey(new_hotkey)

        assert transcriber.hotkey == new_hotkey


# TestUTF8Validation y TestBlockManagement eliminados (v0.13.0) — ver comentarios arriba.


@pytest.mark.unit
class TestClientManagement:
    """Tests for API client management."""

    @pytest.fixture
    def transcriber(self):
        """Create a Transcriber instance."""
        config_manager = Mock()
        config_manager.get = Mock(
            side_effect=lambda k, d=None: {
                "hotkey": "F5",
                "record_mode": "toggle",
                "api_key": "test_key",
                "audio_priority_apps": [],
                "utf8_validation": True,
                "blocks": {},
            }.get(k, d)
        )

        mock_deps = {
            "config_manager": config_manager,
            "sound_manager": Mock(),
            "file_manager": Mock(),
            "update_status_callback": Mock(),
            "transcription_callback": Mock(),
            "localization_manager": Mock(),
            "overlay_callback": Mock(),
        }
        with patch("backend.transcriber.Groq"):
            return Transcriber(**mock_deps)

    def test_reload_client(self, transcriber):
        """Test reloading Groq client."""
        with patch("backend.transcriber.Groq") as mock_groq:
            transcriber.reload_client()

            assert mock_groq.called
