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

import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import numpy as np
import pytest

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.transcriber import Transcriber


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

            assert not transcriber.is_recording
            assert transcriber.hotkey == "F5"
            assert transcriber.record_mode == "toggle"
            assert transcriber.freq == 16000
            assert transcriber.audio_data == []
            assert transcriber.utf8_validation_enabled
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


@pytest.mark.unit
class TestTranscriberRecording:
    """Tests for recording functionality."""

    @pytest.fixture
    def transcriber(self, mock_dependencies):
        """Create a Transcriber instance for testing."""
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

    def test_start_recording(self, transcriber):
        """Test starting audio recording."""
        with patch("backend.transcriber.sd.InputStream"):
            transcriber.start_recording()

            assert transcriber.is_recording
            assert transcriber.audio_data == []
            transcriber.update_status.assert_called()

    def test_stop_recording(self, transcriber):
        """Test stopping audio recording.

        Current verified contract (v0.15.8): stop_recording keeps the audio
        snapshot (process_recording consumes it in its own thread) and the
        buffer is reset on the NEXT start_recording under audio_lock. It
        spawns process_recording via a daemon thread instead of running it
        inline.
        """
        transcriber.is_recording = True
        transcriber.audio_data = [np.array([1, 2, 3])]

        with patch("backend.transcriber.sf.write"), patch(
            "backend.transcriber.threading.Thread"
        ) as mock_thread, patch.object(transcriber, "_push_overlay_event"):
            transcriber.stop_recording()

            assert not transcriber.is_recording
            # Snapshot preserved for process_recording; reset happens on next start
            assert len(transcriber.audio_data) == 1
            # process_recording spawned exactly once
            mock_thread.assert_called_once()

    def test_double_start_recording(self, transcriber):
        """Test that double start recording is prevented."""
        with patch("backend.transcriber.sd.InputStream"):
            transcriber.start_recording()
            transcriber.start_recording()  # Should not start again

            # Verify only one stream was created
            assert transcriber.is_recording


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
        """Test successful transcription with Groq service.

        Current verified contract (faster-whisper eradicated, v0.15.0+):
        transcribe_with_groq returns the transcription TEXT as ``str`` (or
        None on failure). The Groq client is called with
        response_format="text", so create() yields the text directly; block
        results are side metadata and never replace the returned text.
        """
        # Mock Groq client — response_format="text" returns the raw string
        transcriber.cliente.audio.transcriptions.create = Mock(return_value="Texto de prueba")
        # Hermetic unit test: no metadata file writes / generator side effects
        transcriber.metadata_generator = Mock()
        transcriber.metadata_manager = Mock()

        result = transcriber.transcribe_with_groq(temp_audio_file)

        assert isinstance(result, str)
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


@pytest.mark.unit
class TestTextValidation:
    """Tests for text validation functionality."""

    @pytest.fixture
    def mock_dependencies(self):
        """Create mock dependencies with a usable config."""
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
    def transcriber(self, mock_dependencies):
        """Create a Transcriber instance."""
        with patch("backend.transcriber.Groq"):
            return Transcriber(**mock_dependencies)

    def test_validate_text_valid(self, transcriber):
        """Test validation of valid text.

        Current verified contract: validate_text delegates to
        utf8_validator.validate_transcription and returns its tuple
        (is_valid: bool, problems: list[str]).
        """
        transcriber.utf8_validator.validate_transcription = Mock(return_value=(True, []))

        is_valid, problems = transcriber.validate_text("Este es un texto válido.")

        assert is_valid
        assert problems == []
        transcriber.utf8_validator.validate_transcription.assert_called_once_with(
            "Este es un texto válido."
        )

    def test_validate_text_empty(self, transcriber):
        """Test validation of empty text returns problems list."""
        transcriber.utf8_validator.validate_transcription = Mock(
            return_value=(False, ["Texto vacío"])
        )

        is_valid, problems = transcriber.validate_text("")

        assert not is_valid
        assert problems

    def test_validate_text_problems_passed_through(self, transcriber):
        """Test validator problems are returned verbatim (no string mangling).

        Drift note (batch 2): the old test expected a min-length error for
        short text. The current contract has no length concept —
        validate_text is pure delegation to UTF8Validator and returns
        whatever problems list it produces.
        """
        transcriber.utf8_validator.validate_transcription = Mock(return_value=(False, ["Hi"]))

        is_valid, problems = transcriber.validate_text("Hi")

        assert not is_valid
        assert problems == ["Hi"]

    def test_validate_text_none(self, transcriber):
        """Test validation of None text reports a problem, not a crash."""
        transcriber.utf8_validator.validate_transcription = Mock(
            return_value=(False, ["None input"])
        )

        is_valid, problems = transcriber.validate_text(None)

        assert not is_valid
        assert problems


@pytest.mark.unit
class TestBlockProcessing:
    """Tests for block processing functionality."""

    @pytest.fixture
    def mock_dependencies(self):
        """Create mock dependencies with a usable config."""
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
    def transcriber(self, mock_dependencies):
        """Create a Transcriber instance."""
        with patch("backend.transcriber.Groq"):
            return Transcriber(**mock_dependencies)

    def test_process_with_blocks_enabled(self, transcriber):
        """Test processing text with blocks enabled.

        Current verified contract: blocks add SIDE metadata only — the
        returned text is always the original transcription.
        """
        block_result = Mock()
        block_result.success = True
        block_result.metadata = {"block_name": "task_extractor"}
        transcriber.block_manager.process = Mock(return_value=[block_result])

        result = transcriber._process_with_blocks("Texto original")

        assert result == "Texto original"
        transcriber.block_manager.process.assert_called_once()

    def test_process_with_blocks_disabled(self, transcriber):
        """Test processing text when no block produces results."""
        transcriber.block_manager.process = Mock(return_value=[])

        result = transcriber._process_with_blocks("Texto original")

        assert result == "Texto original"
        transcriber.block_manager.process.assert_called_once()

    def test_get_block_results(self, transcriber):
        """Test getting block results.

        Current verified contract: get_block_results returns the transcriber's
        own ``last_block_results`` side-metadata list (defaulting to []).
        """
        mock_results = [
            {"block": "task_extractor", "result": ["Tarea 1"]},
            {"block": "summary", "result": "Resumen"},
        ]
        transcriber.last_block_results = mock_results

        results = transcriber.get_block_results()

        assert results == mock_results

    def test_get_block_stats(self, transcriber):
        """Test getting block statistics."""
        mock_stats = {"total_blocks": 3, "enabled_blocks": 2, "executed_blocks": 2}
        transcriber.block_manager.get_stats = Mock(return_value=mock_stats)

        stats = transcriber.get_block_stats()

        assert stats == mock_stats


@pytest.mark.unit
class TestHotkeyManagement:
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


@pytest.mark.unit
class TestUTF8Validation:
    """Tests for UTF-8 validation functionality."""

    @pytest.fixture
    def mock_dependencies(self):
        """Create mock dependencies with a usable config."""
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
    def transcriber(self, mock_dependencies):
        """Create a Transcriber instance."""
        with patch("backend.transcriber.Groq"):
            return Transcriber(**mock_dependencies)

    def test_validate_transcription_utf8_valid(self, transcriber):
        """Test UTF-8 validation of valid text.

        Current verified contract: validate_transcription_utf8 delegates to
        utf8_validator.validate_transcription (tuple contract) and returns
        the text unchanged when it is already valid.
        """
        text = "Este es un texto con ñ y áéíóú."
        transcriber.utf8_validator.validate_transcription = Mock(return_value=(True, []))

        result = transcriber.validate_transcription_utf8(text)

        assert result == text
        transcriber.utf8_validator.validate_transcription.assert_called_once_with(text)

    def test_update_utf8_validation(self, transcriber):
        """Test updating UTF-8 validation setting."""
        transcriber.update_utf8_validation(False)

        assert not transcriber.utf8_validation_enabled

        transcriber.update_utf8_validation(True)

        assert transcriber.utf8_validation_enabled


@pytest.mark.unit
class TestBlockManagement:
    """Tests for block management functionality."""

    @pytest.fixture
    def mock_dependencies(self):
        """Create mock dependencies with a usable config."""
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
    def transcriber(self, mock_dependencies):
        """Create a Transcriber instance."""
        with patch("backend.transcriber.Groq"):
            return Transcriber(**mock_dependencies)

    def test_enable_block(self, transcriber):
        """Test enabling a block delegates to the block manager."""
        transcriber.block_manager = Mock()
        transcriber.block_manager.enable_block = Mock(return_value=True)

        result = transcriber.enable_block("task_extractor")

        assert result
        transcriber.block_manager.enable_block.assert_called_with("task_extractor")

    def test_disable_block(self, transcriber):
        """Test disabling a block delegates to the block manager."""
        transcriber.block_manager = Mock()
        transcriber.block_manager.disable_block = Mock(return_value=True)

        result = transcriber.disable_block("summary")

        assert result
        transcriber.block_manager.disable_block.assert_called_with("summary")

    def test_reload_blocks(self, transcriber):
        """Test reloading blocks configuration.

        Current verified contract: reload_blocks builds a FRESH BlockManager
        and re-runs _setup_blocks from the current config.
        """
        old_block_manager = transcriber.block_manager
        with patch("backend.transcriber.BlockManager") as mock_bm_cls, patch.object(
            transcriber, "_setup_blocks"
        ) as mock_setup:
            transcriber.reload_blocks()

            mock_bm_cls.assert_called_once()
            mock_setup.assert_called_once()
        assert transcriber.block_manager is not old_block_manager


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
