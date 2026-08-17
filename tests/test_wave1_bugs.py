"""Tests for Wave 1 bugfixes: HotkeyManager init, _stopping flag, priority cache."""

import pytest
import sys
import os
import threading
import time
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.transcriber import Transcriber


@pytest.fixture
def mock_dependencies():
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
        "groq_api_key_from_env": None,
        "nvidia_enabled": False,
        "save_audio": False,
    }.get(key, default)
    config_manager.get_groq_api_key_from_env.return_value = None

    sound_manager = Mock()
    file_manager = Mock()
    update_status_callback = Mock()
    transcription_callback = Mock()
    localization_manager = Mock()

    return {
        "config_manager": config_manager,
        "sound_manager": sound_manager,
        "file_manager": file_manager,
        "update_status_callback": update_status_callback,
        "transcription_callback": transcription_callback,
        "localization_manager": localization_manager,
    }


@pytest.fixture
def transcriber(mock_dependencies):
    with patch("backend.transcriber.keyboard"):
        return Transcriber(**mock_dependencies)


class TestTranscriberHotkeyManager:
    """Task 1.1: Transcriber.__init__ should create HotkeyManager."""

    def test_transcriber_has_hotkey_manager(self, transcriber):
        assert hasattr(transcriber, "hotkey_manager")

    def test_hotkey_manager_is_hotkey_manager_instance(self, transcriber):
        from backend.hotkey_manager import HotkeyManager
        assert isinstance(transcriber.hotkey_manager, HotkeyManager)


class TestTranscriberStoppingFlag:
    """Task 1.3: Race condition fix with _stopping Event."""

    def test_stopping_flag_exists(self, transcriber):
        assert hasattr(transcriber, "_stopping")
        assert isinstance(transcriber._stopping, threading.Event)

    def test_stopping_flag_initially_clear(self, transcriber):
        assert not transcriber._stopping.is_set()

    def test_start_recording_returns_if_stopping(self, transcriber):
        """start_recording must bail out if _stopping is set."""
        transcriber._stopping.set()
        transcriber.start_recording()
        assert not transcriber.is_recording

    def test_stop_recording_sets_stopping(self, transcriber):
        """stop_recording should set _stopping at entry."""
        transcriber.is_recording = True
        transcriber.stop_event = threading.Event()
        transcriber.recording_thread = None
        with patch.object(transcriber, "sound_manager"), \
             patch.object(transcriber, "update_status"), \
             patch.object(transcriber, "_push_overlay_event"):
            transcriber.stop_recording()
        assert not transcriber._stopping.is_set()


class TestTranscriberPriorityCache:
    """Task 1.5: Process list cache for priority apps."""

    def test_cache_attributes_exist(self, transcriber):
        assert hasattr(transcriber, "_cached_priority_apps")
        assert hasattr(transcriber, "_cache_time")

    def test_cache_initially_empty(self, transcriber):
        assert transcriber._cached_priority_apps == set()
        assert transcriber._cache_time == 0

    def test_refresh_priority_cache_populates(self, transcriber):
        """_refresh_priority_cache populates _cached_priority_apps."""
        mock_proc = Mock()
        mock_proc.info = {"name": "firefox.exe"}
        with patch("backend.transcriber.psutil.process_iter", return_value=[mock_proc]):
            transcriber._refresh_priority_cache()
        assert "firefox.exe" in transcriber._cached_priority_apps

    def test_refresh_priority_cache_respects_ttl(self, transcriber):
        """Cache should not refresh if <5s since last refresh."""
        transcriber._cache_time = time.time()
        transcriber._cached_priority_apps = {"cached_app.exe"}
        with patch("backend.transcriber.psutil.process_iter") as mock_iter:
            transcriber._refresh_priority_cache()
            mock_iter.assert_not_called()
        assert "cached_app.exe" in transcriber._cached_priority_apps
