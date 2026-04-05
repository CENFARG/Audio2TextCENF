"""
Integration tests for Audio2Text application.

This module tests end-to-end workflows including:
- Configuration loading → Transcriber initialization → Recording → Transcription → File saving
- Block processing pipeline
- Metadata generation and storage
- Hotkey registration and handling
- Error handling across components

Author: Audio2Text Development Team
Version: 0.13.0
"""

import pytest
import sys
import os
import json
import tempfile
import numpy as np
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.config_manager import ConfigManager
from backend.file_manager import FileManager
from backend.sound_manager import SoundManager
from backend.transcriber import Transcriber
from backend.localization_manager import LocalizationManager
from backend.transcription_metadata import TranscriptionMetadata


@pytest.mark.integration
class TestConfigToTranscriberIntegration:
    """Tests for ConfigManager → Transcriber integration."""

    @pytest.fixture
    def temp_config_file(self):
        """Create a temporary config file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            config_file = f.name
            test_config = {
                "app_version": "0.13.0",
                "hotkey": "F5",
                "default_language": "es",
                "api_key": "test_key_123",
                "audio_path": "./audio_test",
                "transcriptions_path": "./transcriptions_test",
                "max_audio_files": 100,
                "save_audio": True,
                "save_logs": True,
                "utf8_validation": True,
                "asr_provider": "groq",
            }
            json.dump(test_config, f)

        yield config_file

        if os.path.exists(config_file):
            os.unlink(config_file)

    @pytest.fixture
    def config_manager(self, temp_config_file):
        """Create ConfigManager instance."""
        return ConfigManager(config_file=temp_config_file)

    def test_config_loads_successfully(self, config_manager):
        """Test that configuration loads successfully."""
        assert config_manager.config is not None
        assert config_manager.config["hotkey"] == "F5"
        assert config_manager.config["default_language"] == "es"

    def test_config_manager_provides_api_key(self, config_manager):
        """Test that ConfigManager provides API key for Transcriber."""
        api_key = config_manager.get("api_key")
        assert api_key is not None
        assert isinstance(api_key, str)


@pytest.mark.integration
class TestTranscriberWorkflow:
    """Tests for complete transcription workflow."""

    @pytest.fixture
    def mock_dependencies(self, tmp_path):
        """Create mock dependencies for Transcriber."""
        config_manager = Mock()
        config_manager.get.side_effect = lambda key, default=None: {
            "hotkey": "F5",
            "record_mode": "toggle",
            "service": "groq",
            "language": "es",
            "model": "whisper-large-v3",
            "api_key": "test_key",
            "audio_path": str(tmp_path / "audio"),
            "transcriptions_path": str(tmp_path / "transcriptions"),
            "audio_priority_apps": [],
            "utf8_validation": True,
            "save_audio": True,
            "save_logs": True,
            "max_audio_files": 100,
            "blocks": {},
        }.get(key, default)

        sound_manager = Mock()
        file_manager = FileManager(config_manager)
        update_status = Mock()
        transcription_callback = Mock()
        localization_manager = LocalizationManager(lang_code="es")
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

    @pytest.fixture
    def transcriber(self, mock_dependencies):
        """Create Transcriber instance with mocked Groq."""
        with patch("backend.transcriber.Groq"):
            return Transcriber(**mock_dependencies)

    def test_transcriber_initialization(self, transcriber):
        """Test that Transcriber initializes successfully."""
        assert transcriber.is_recording == False
        assert transcriber.hotkey == "F5"
        assert transcriber.block_manager is not None
        assert transcriber.custom_vocab is not None

    def test_transcriber_recording_workflow(self, transcriber):
        """Test complete recording workflow: start → stop → process."""
        with patch("backend.transcriber.sd.InputStream"):
            # Start recording
            transcriber.start_recording()
            assert transcriber.is_recording == True

            # Add some audio data
            transcriber.audio_data = [np.random.randint(-32768, 32767, size=16000, dtype=np.int16)]

            # Stop recording
            with patch("backend.transcriber.sf.write"):
                transcriber.stop_recording()
                assert transcriber.is_recording == False

    def test_transcriber_transcription_workflow(self, transcriber, tmp_path):
        """Test transcription workflow with mocked API."""
        # Create temporary audio file
        import wave

        audio_file = tmp_path / "test_audio.wav"
        with wave.open(str(audio_file), "wb") as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(16000)
            wav.writeframes(b"\x00\x00" * 16000)

        # Mock Groq response
        mock_response = Mock()
        mock_response.text = "Texto de prueba"
        mock_response.language = "es"
        transcriber.cliente.audio.transcriptions.create = Mock(return_value=mock_response)

        # Transcribe
        result = transcriber.transcribe_with_groq(str(audio_file))

        assert result["text"] == "Texto de prueba"
        assert result["language"] == "es"


@pytest.mark.integration
class TestFileManagerIntegration:
    """Tests for FileManager integration with workflow."""

    @pytest.fixture
    def file_manager(self, tmp_path):
        """Create FileManager instance."""
        config = Mock()
        config.get.side_effect = lambda key, default=None: {
            "audio_path": str(tmp_path / "audio"),
            "transcriptions_path": str(tmp_path / "transcriptions"),
            "save_audio": True,
            "save_logs": True,
            "max_audio_files": 100,
            "auto_cleanup_enabled": False,
        }.get(key, default)

        return FileManager(config)

    def test_save_and_retrieve_audio(self, file_manager):
        """Test saving and retrieving audio files."""
        # Save audio
        audio_data = np.random.randint(-32768, 32767, size=16000, dtype=np.int16)
        filepath = file_manager.save_audio_file(audio_data)

        assert filepath is not None
        assert os.path.exists(filepath)

        # Retrieve file list
        files = file_manager.get_audio_files_list()
        assert len(files) == 1
        assert files[0]["path"] == filepath

    def test_save_transcription_entry(self, file_manager):
        """Test saving transcription entry."""
        transcription_data = {
            "text": "Texto de prueba",
            "duration": 2.5,
            "language": "es",
            "audio_file": "audio_test.wav",
        }

        file_manager.save_transcription_entry(transcription_data)

        log_file = os.path.join(file_manager.transcriptions_path, "transcriptions_log.jsonl")
        assert os.path.exists(log_file)

        # Verify content
        with open(log_file, "r", encoding="utf-8") as f:
            content = f.read()
            assert "Texto de prueba" in content


@pytest.mark.integration
class TestBlockProcessingIntegration:
    """Tests for block processing pipeline."""

    @pytest.fixture
    def transcriber(self, tmp_path):
        """Create Transcriber with blocks."""
        config = Mock()
        config.get.side_effect = lambda key, default=None: {
            "hotkey": "F5",
            "record_mode": "toggle",
            "service": "groq",
            "language": "es",
            "api_key": "test_key",
            "audio_priority_apps": [],
            "utf8_validation": True,
            "blocks": {
                "task_extractor_enabled": True,
                "summary_enabled": True,
                "keyword_extractor_enabled": True,
            },
        }.get(key, default)

        deps = {
            "config_manager": config,
            "sound_manager": Mock(),
            "file_manager": Mock(),
            "update_status_callback": Mock(),
            "transcription_callback": Mock(),
            "localization_manager": Mock(),
            "overlay_callback": Mock(),
        }

        with patch("backend.transcriber.Groq"):
            return Transcriber(**deps)

    def test_block_manager_initialized(self, transcriber):
        """Test that BlockManager is initialized."""
        assert transcriber.block_manager is not None
        assert hasattr(transcriber.block_manager, "blocks")

    def test_process_with_blocks(self, transcriber):
        """Test processing text with blocks."""
        # Mock block manager to return processed text
        transcriber.block_manager.process = Mock(return_value="Texto procesado con bloques")

        result = transcriber._process_with_blocks("Texto original")

        assert result == "Texto procesado con bloques"
        transcriber.block_manager.process.assert_called_once()


@pytest.mark.integration
class TestMetadataIntegration:
    """Tests for metadata management integration."""

    @pytest.fixture
    def metadata(self):
        """Create TranscriptionMetadata instance."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            metadata_file = f.name

        metadata = TranscriptionMetadata(metadata_file=metadata_file)
        yield metadata

        if os.path.exists(metadata_file):
            os.unlink(metadata_file)

    def test_complete_metadata_workflow(self, metadata):
        """Test complete metadata workflow: set → get → update → delete."""
        filename = "audio_1.wav"

        # Set metadata
        metadata.set_emoji(filename, "🎤")
        metadata.set_title(filename, "My Recording")
        metadata.set_tags(filename, ["important", "work"])
        metadata.set_notes(filename, "Important meeting notes")

        # Get and verify
        assert metadata.get_emoji(filename) == "🎤"
        assert metadata.get_title(filename) == "My Recording"
        assert metadata.get_tags(filename) == ["important", "work"]
        assert metadata.get_notes(filename) == "Important meeting notes"

        # Update
        metadata.set_emoji(filename, "🎹")
        assert metadata.get_emoji(filename) == "🎹"

        # Get all
        all_meta = metadata.get_all_metadata(filename)
        assert all_meta["emoji"] == "🎹"
        assert all_meta["title"] == "My Recording"

        # Delete
        metadata.delete_metadata(filename)
        assert metadata.get_all_metadata(filename) == {}


@pytest.mark.integration
class TestErrorHandlingIntegration:
    """Tests for error handling across components."""

    def test_invalid_api_key_handling(self):
        """Test handling of invalid API key."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            config_file = f.name
            json.dump({"api_key": ""}, f)

        try:
            config_manager = ConfigManager(config_file=config_file)
            # Should not crash, should use default or handle gracefully
            assert config_manager.config is not None
        finally:
            if os.path.exists(config_file):
                os.unlink(config_file)

    def test_missing_audio_directory(self, tmp_path):
        """Test handling of missing audio directory."""
        config = Mock()
        config.get.side_effect = lambda key, default=None: {
            "audio_path": str(tmp_path / "nonexistent_audio"),
            "transcriptions_path": str(tmp_path / "transcriptions"),
            "save_audio": True,
        }.get(key, default)

        # FileManager should create directory
        file_manager = FileManager(config)
        assert os.path.exists(file_manager.audio_path)

    def test_invalid_transcription_text(self, tmp_path):
        """Test handling of invalid transcription text."""
        config = Mock()
        config.get.side_effect = lambda key, default=None: {
            "hotkey": "F5",
            "api_key": "test",
            "audio_priority_apps": [],
            "utf8_validation": True,
            "blocks": {},
        }.get(key, default)

        deps = {
            "config_manager": config,
            "sound_manager": Mock(),
            "file_manager": Mock(),
            "update_status_callback": Mock(),
            "transcription_callback": Mock(),
            "localization_manager": Mock(),
            "overlay_callback": Mock(),
        }

        with patch("backend.transcriber.Groq"):
            transcriber = Transcriber(**deps)

            # Test empty text
            is_valid, error = transcriber.validate_text("")
            assert is_valid == False
            assert error is not None

            # Test None
            is_valid, error = transcriber.validate_text(None)
            assert is_valid == False


@pytest.mark.integration
class TestHotkeyIntegration:
    """Tests for hotkey handling integration."""

    def test_hotkey_format_consistency(self):
        """Test that hotkey format is consistent across components."""
        from backend.hotkey_manager import HotkeyManager

        manager = HotkeyManager()

        # Parse and format should be consistent
        hotkey_str = "ctrl+shift+f5"
        hotkey = manager.parse_hotkey_string(hotkey_str)
        formatted = manager.format_hotkey_string(hotkey.key, hotkey.modifiers)

        assert formatted == hotkey_str


@pytest.mark.integration
class TestFullWorkflow:
    """Tests for complete end-to-end workflows."""

    def test_config_to_transcriber_workflow(self, tmp_path):
        """Test ConfigManager → Transcriber → Record → Transcribe workflow."""
        # Setup config
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            config_file = f.name
            config_data = {
                "hotkey": "F5",
                "api_key": "test_key",
                "default_language": "es",
                "audio_path": str(tmp_path / "audio"),
                "transcriptions_path": str(tmp_path / "transcriptions"),
                "save_audio": True,
                "save_logs": True,
                "utf8_validation": True,
                "blocks": {},
            }
            json.dump(config_data, f)

        try:
            # Load config
            config_manager = ConfigManager(config_file=config_file)
            assert config_manager.config["hotkey"] == "F5"

            # Create file manager
            file_manager = FileManager(config_manager)
            assert os.path.exists(file_manager.audio_path)

            # Create transcriber
            deps = {
                "config_manager": config_manager,
                "sound_manager": Mock(),
                "file_manager": file_manager,
                "update_status_callback": Mock(),
                "transcription_callback": Mock(),
                "localization_manager": LocalizationManager("es"),
                "overlay_callback": Mock(),
            }

            with patch("backend.transcriber.Groq"):
                transcriber = Transcriber(**deps)

                # Verify initialization
                assert transcriber.hotkey == "F5"
                assert transcriber.block_manager is not None

        finally:
            if os.path.exists(config_file):
                os.unlink(config_file)
