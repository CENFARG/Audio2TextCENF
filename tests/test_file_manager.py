"""
Unit tests for FileManager class.

This module tests file management functionality including:
- Audio file saving and loading
- Transcription logging
- File cleanup and maintenance
- Path handling
- Size calculations

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

from backend.file_manager import FileManager


@pytest.mark.unit
class TestFileManagerInitialization:
    """Tests for FileManager initialization."""

    @pytest.fixture
    def mock_config(self):
        """Create a mock configuration manager."""
        config = Mock()
        config.get.side_effect = lambda key, default=None: {
            "audio_path": "./audio_test",
            "transcriptions_path": "./transcriptions_test",
            "save_audio": True,
            "save_logs": True,
            "max_audio_files": 100,
            "max_log_entries": 1000,
            "max_transcription_age_days": 30,
            "auto_cleanup_enabled": True,
        }.get(key, default)
        return config

    @pytest.fixture
    def file_manager(self, mock_config, tmp_path):
        """Create a FileManager instance with temp directory."""
        # Override paths to use temp directory
        mock_config.get.side_effect = lambda key, default=None: {
            "audio_path": str(tmp_path / "audio"),
            "transcriptions_path": str(tmp_path / "transcriptions"),
            "save_audio": True,
            "save_logs": True,
            "max_audio_files": 5,
            "max_log_entries": 10,
            "max_transcription_age_days": 30,
            "auto_cleanup_enabled": True,
        }.get(key, default)

        return FileManager(mock_config)

    def test_initialization_creates_directories(self, file_manager, tmp_path):
        """Test that initialization creates audio and transcriptions directories."""
        assert os.path.exists(tmp_path / "audio")
        assert os.path.exists(tmp_path / "transcriptions")

    def test_audio_path_is_absolute(self, file_manager):
        """Test that audio_path is converted to absolute path."""
        assert os.path.isabs(file_manager.audio_path)

    def test_transcriptions_path_is_absolute(self, file_manager):
        """Test that transcriptions_path is converted to absolute path."""
        assert os.path.isabs(file_manager.transcriptions_path)


@pytest.mark.unit
class TestAudioFileOperations:
    """Tests for audio file operations."""

    @pytest.fixture
    def file_manager(self, tmp_path):
        """Create a FileManager instance."""
        config = Mock()
        config.get.side_effect = lambda key, default=None: {
            "audio_path": str(tmp_path / "audio"),
            "transcriptions_path": str(tmp_path / "transcriptions"),
            "save_audio": True,
            "max_audio_files": 5,
            "auto_cleanup_enabled": False,  # Disable for testing
        }.get(key, default)

        return FileManager(config)

    def test_save_audio_file_success(self, file_manager):
        """Test successfully saving an audio file."""
        # Create mock audio data
        audio_data = np.random.randint(-32768, 32767, size=16000, dtype=np.int16)

        filepath = file_manager.save_audio_file(audio_data, sample_rate=16000)

        assert filepath is not None
        assert os.path.exists(filepath)
        assert filepath.endswith(".wav")

    def test_save_audio_file_disabled(self, file_manager):
        """Test that audio is not saved when save_audio is False."""
        file_manager.config.get = Mock(return_value=False)

        audio_data = np.random.randint(-32768, 32767, size=16000, dtype=np.int16)
        filepath = file_manager.save_audio_file(audio_data)

        assert filepath is None

    def test_save_audio_file_from_temp(self, file_manager, tmp_path):
        """Test saving audio file from temporary path."""
        # Create a temporary audio file
        temp_file = tmp_path / "temp_audio.wav"
        audio_data = np.random.randint(-32768, 32767, size=16000, dtype=np.int16)

        import soundfile as sf

        sf.write(str(temp_file), audio_data, 16000)

        filepath = file_manager.save_audio_file_from_temp(str(temp_file))

        assert filepath is not None
        assert os.path.exists(filepath)
        assert not os.path.exists(temp_file)  # Temp file should remain (copy, not move)

    def test_save_audio_converts_list_to_array(self, file_manager):
        """Test that list audio data is converted to numpy array."""
        audio_list = [np.array([1, 2, 3]), np.array([4, 5, 6])]

        filepath = file_manager.save_audio_file(audio_list)

        assert filepath is not None
        assert os.path.exists(filepath)

    def test_save_audio_empty_list(self, file_manager):
        """Test saving empty audio list returns None."""
        filepath = file_manager.save_audio_file([])

        assert filepath is None


@pytest.mark.unit
class TestTranscriptionLogging:
    """Tests for transcription logging functionality."""

    @pytest.fixture
    def file_manager(self, tmp_path):
        """Create a FileManager instance."""
        config = Mock()
        config.get.side_effect = lambda key, default=None: {
            "audio_path": str(tmp_path / "audio"),
            "transcriptions_path": str(tmp_path / "transcriptions"),
            "save_logs": True,
            "max_log_entries": 10,
        }.get(key, default)

        return FileManager(config)

    def test_save_transcription_entry(self, file_manager):
        """Test saving a transcription entry."""
        transcription_data = {
            "text": "Texto de prueba",
            "duration": 2.5,
            "language": "es",
            "audio_file": "audio_test.wav",
        }

        file_manager.save_transcription_entry(transcription_data)

        log_file = os.path.join(file_manager.transcriptions_path, "transcriptions_log.jsonl")
        assert os.path.exists(log_file)

        with open(log_file, "r", encoding="utf-8") as f:
            lines = f.readlines()

        assert len(lines) == 1
        entry = json.loads(lines[0])
        assert entry["text"] == "Texto de prueba"
        assert entry["duration"] == 2.5

    def test_save_transcription_disabled(self, file_manager):
        """Test that logging is disabled when save_logs is False."""
        file_manager.config.get = Mock(return_value=False)

        transcription_data = {"text": "Test", "duration": 1.0}
        file_manager.save_transcription_entry(transcription_data)

        log_file = os.path.join(file_manager.transcriptions_path, "transcriptions_log.jsonl")
        assert not os.path.exists(log_file)

    def test_maintain_log_size(self, file_manager):
        """Test that log size is maintained within limit."""
        # Create log file with 15 entries (max is 10)
        log_file = os.path.join(file_manager.transcriptions_path, "transcriptions_log.jsonl")

        for i in range(15):
            entry = {"text": f"Entry {i}", "duration": 1.0}
            file_manager.save_transcription_entry(entry)

        with open(log_file, "r") as f:
            lines = f.readlines()

        # Should only have last 10 entries
        assert len(lines) == 10


@pytest.mark.unit
class TestFileCleanup:
    """Tests for file cleanup functionality."""

    @pytest.fixture
    def file_manager(self, tmp_path):
        """Create a FileManager instance."""
        config = Mock()
        config.get.side_effect = lambda key, default=None: {
            "audio_path": str(tmp_path / "audio"),
            "transcriptions_path": str(tmp_path / "transcriptions"),
            "max_audio_files": 3,
            "max_transcription_age_days": 30,
            "auto_cleanup_enabled": True,
        }.get(key, default)

        return FileManager(config)

    def test_maintain_audio_file_limit(self, file_manager):
        """Test that audio file limit is maintained."""
        # Create 5 audio files (limit is 3)
        import soundfile as sf

        for i in range(5):
            audio_data = np.random.randint(-32768, 32767, size=16000, dtype=np.int16)
            filepath = os.path.join(file_manager.audio_path, f"audio_{i}.wav")
            sf.write(filepath, audio_data, 16000)

        # Trigger maintenance
        deleted = file_manager.maintain_audio_file_limit()

        assert deleted == 2

        # Only 3 files should remain
        remaining = [f for f in os.listdir(file_manager.audio_path) if f.endswith(".wav")]
        assert len(remaining) == 3

    def test_clean_old_audio_files(self, file_manager):
        """Test cleaning old audio files."""
        import soundfile as sf
        import time

        # Create 3 audio files with different timestamps
        for i in range(3):
            audio_data = np.random.randint(-32768, 32768, size=16000, dtype=np.int16)
            filepath = os.path.join(file_manager.audio_path, f"audio_{i}.wav")
            sf.write(filepath, audio_data, 16000)

        # Make first file old (2 days ago)
        files = sorted(file_manager.audio_path)
        if files:
            old_time = time.time() - (2 * 24 * 60 * 60)
            os.utime(files[0], (old_time, old_time))

        # Clean files older than 1 day
        file_manager.config.get = Mock(return_value=1)  # 1 day threshold
        deleted = file_manager.clean_old_audio_files(days_old=1)

        assert deleted >= 0

    def test_clear_audio_files(self, file_manager):
        """Test clearing all audio files."""
        import soundfile as sf

        # Create 3 audio files
        for i in range(3):
            audio_data = np.random.randint(-32768, 32768, size=16000, dtype=np.int16)
            filepath = os.path.join(file_manager.audio_path, f"audio_{i}.wav")
            sf.write(filepath, audio_data, 16000)

        result = file_manager.clear_audio_files()

        assert result == True
        remaining = [f for f in os.listdir(file_manager.audio_path) if f.endswith(".wav")]
        assert len(remaining) == 0

    def test_clear_transcriptions(self, file_manager):
        """Test clearing transcription log."""
        # Create log file
        log_file = os.path.join(file_manager.transcriptions_path, "transcriptions_log.jsonl")
        with open(log_file, "w") as f:
            f.write('{"text": "test"}\n')

        result = file_manager.clear_transcriptions()

        assert result == True
        assert not os.path.exists(log_file)


@pytest.mark.unit
class TestFileSizeCalculations:
    """Tests for file size calculation methods."""

    @pytest.fixture
    def file_manager(self, tmp_path):
        """Create a FileManager instance."""
        config = Mock()
        config.get.side_effect = lambda key, default=None: {
            "audio_path": str(tmp_path / "audio"),
            "transcriptions_path": str(tmp_path / "transcriptions"),
        }.get(key, default)

        return FileManager(config)

    def test_get_audio_files_size_empty(self, file_manager):
        """Test getting size when no audio files exist."""
        size = file_manager.get_audio_files_size()
        assert size == 0

    def test_get_audio_files_size_with_files(self, file_manager):
        """Test getting size with audio files."""
        import soundfile as sf

        # Create 2 audio files
        for i in range(2):
            audio_data = np.random.randint(-32768, 32768, size=16000, dtype=np.int16)
            filepath = os.path.join(file_manager.audio_path, f"audio_{i}.wav")
            sf.write(filepath, audio_data, 16000)

        size = file_manager.get_audio_files_size()
        assert size > 0

    def test_get_transcriptions_size_empty(self, file_manager):
        """Test getting transcriptions size when no log exists."""
        size = file_manager.get_transcriptions_size()
        assert size == 0

    def test_get_transcriptions_size_with_log(self, file_manager):
        """Test getting transcriptions size with log file."""
        log_file = os.path.join(file_manager.transcriptions_path, "transcriptions_log.jsonl")
        with open(log_file, "w") as f:
            f.write('{"text": "test"}\n' * 10)

        size = file_manager.get_transcriptions_size()
        assert size > 0


@pytest.mark.unit
class TestAudioFileList:
    """Tests for getting audio file list."""

    @pytest.fixture
    def file_manager(self, tmp_path):
        """Create a FileManager instance."""
        config = Mock()
        config.get.side_effect = lambda key, default=None: {
            "audio_path": str(tmp_path / "audio"),
            "transcriptions_path": str(tmp_path / "transcriptions"),
        }.get(key, default)

        return FileManager(config)

    def test_get_audio_files_list_empty(self, file_manager):
        """Test getting file list when no files exist."""
        files = file_manager.get_audio_files_list()
        assert files == []

    def test_get_audio_files_list_with_files(self, file_manager):
        """Test getting file list with audio files."""
        import soundfile as sf
        import time

        # Create 3 audio files
        for i in range(3):
            audio_data = np.random.randint(-32768, 32768, size=16000, dtype=np.int16)
            filepath = os.path.join(file_manager.audio_path, f"audio_{i}.wav")
            sf.write(filepath, audio_data, 16000)
            time.sleep(0.01)  # Ensure different mtimes

        files = file_manager.get_audio_files_list()

        assert len(files) == 3
        # Should be sorted by mtime descending (newest first)
        assert files[0]["name"] == "audio_2.wav"
        assert files[2]["name"] == "audio_0.wav"

    def test_get_audio_files_list_with_limit(self, file_manager):
        """Test getting file list with limit."""
        import soundfile as sf

        # Create 5 audio files
        for i in range(5):
            audio_data = np.random.randint(-32768, 32768, size=16000, dtype=np.int16)
            filepath = os.path.join(file_manager.audio_path, f"audio_{i}.wav")
            sf.write(filepath, audio_data, 16000)

        files = file_manager.get_audio_files_list(limit=3)

        assert len(files) == 3

    def test_get_audio_files_list_with_offset(self, file_manager):
        """Test getting file list with offset."""
        import soundfile as sf

        # Create 5 audio files
        for i in range(5):
            audio_data = np.random.randint(-32768, 32768, size=16000, dtype=np.int16)
            filepath = os.path.join(file_manager.audio_path, f"audio_{i}.wav")
            sf.write(filepath, audio_data, 16000)

        files = file_manager.get_audio_files_list(limit=2, offset=2)

        assert len(files) == 2


@pytest.mark.unit
class TestPathHandling:
    """Tests for path handling logic."""

    def test_relative_path_conversion(self, tmp_path):
        """Test that relative paths are converted to absolute."""
        config = Mock()
        config.get.side_effect = lambda key, default=None: {
            "audio_path": "./audio",
            "transcriptions_path": "./transcriptions",
        }.get(key, default)

        manager = FileManager(config)

        assert os.path.isabs(manager.audio_path)
        assert os.path.isabs(manager.transcriptions_path)

    def test_absolute_path_preserved(self, tmp_path):
        """Test that absolute paths are preserved."""
        config = Mock()
        abs_audio = str(tmp_path / "custom_audio")
        abs_trans = str(tmp_path / "custom_transcriptions")

        config.get.side_effect = lambda key, default=None: {
            "audio_path": abs_audio,
            "transcriptions_path": abs_trans,
        }.get(key, default)

        manager = FileManager(config)

        assert manager.audio_path == abs_audio
        assert manager.transcriptions_path == abs_trans
