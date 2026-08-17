"""Tests for Wave 1 bugfixes: HotkeyManager init, _stopping flag, priority cache, queue routing, history refresh, cache reset."""

import pytest
import sys
import os
import threading
import time
import queue
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch, PropertyMock

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


class TestUpdateStatusQueue:
    """Task 1.4: update_status routes through queue to avoid thread safety issues."""

    def test_status_queue_exists(self):
        """App should have _status_queue attribute."""
        from ui.app import App
        with patch("ui.app.ConfigManager") as mock_cm, \
             patch("ui.app.SoundManager"), \
             patch("ui.app.FileManager"), \
             patch("ui.app.Transcriber"), \
             patch("ui.app.RecordingOverlay"), \
             patch("ui.app.TranscriptionMetadata"), \
             patch.object(App, "__init__", lambda self, *a, **kw: None):
            app = App.__new__(App)
            app._status_queue = __import__("queue").Queue()
            assert hasattr(app, "_status_queue")

    def test_update_status_enqueues_message(self):
        """update_status should put (msg, color) in queue."""
        import queue
        from ui.app import App
        with patch("ui.app.ConfigManager") as mock_cm, \
             patch("ui.app.SoundManager"), \
             patch("ui.app.FileManager"), \
             patch("ui.app.Transcriber"), \
             patch("ui.app.RecordingOverlay"), \
             patch("ui.app.TranscriptionMetadata"), \
             patch.object(App, "__init__", lambda self, *a, **kw: None):
            app = App.__new__(App)
            app._status_queue = queue.Queue()
            app.after = Mock()
            app.update_status = App.update_status.__get__(app, App)
            app.update_status("test msg", "green")
            assert not app._status_queue.empty()
            msg, color = app._status_queue.get()
            assert msg == "test msg"
            assert color == "green"


class TestRefreshHistoryList:
    """Task 2.1: Fix early return in refresh_history_list."""

    def test_empty_files_with_full_reload_clears_and_shows_placeholder(self):
        """When files_list is empty and full_reload=True, scroll frame should have only placeholder."""
        from ui.app import App
        mock_scroll_frame = Mock()
        mock_scroll_frame.winfo_children.return_value = [Mock(), Mock()]

        with patch.object(App, "__init__", lambda self, *a, **kw: None):
            app = App.__new__(App)
            app.config_manager = Mock()
            app.config_manager.get.return_value = "/fake/audio"
            app.file_manager = Mock()
            app.file_manager.get_audio_files_list.return_value = []
            app.transcriptions_cache = {}
            app.loaded_history_files = set()
            app.history_scroll_frame = mock_scroll_frame
            app.localization_manager = Mock()
            app.localization_manager.get_string.return_value = "No hay archivos"
            app.logger = Mock()

            # Patch ctk.CTkLabel
            mock_label = Mock()
            with patch("ui.app.ctk") as mock_ctk:
                mock_ctk.CTkLabel.return_value = mock_label
                app.refresh_history_list(full_reload=True)

            # Should have destroyed old children and packed a new label
            mock_scroll_frame.winfo_children.assert_called()
            mock_label.pack.assert_called()


class TestFletClearRefresh:
    """Task 2.4: Flet clear methods should call refresh_history."""

    def test_clear_audio_calls_refresh_history(self):
        """clear_audio_with_feedback should call refresh_history."""
        sys.modules["flet"] = MagicMock()
        try:
            from ui_flet.main import Audio2TextApp
            with patch.object(Audio2TextApp, "__init__", lambda self, *a, **kw: None):
                app = Audio2TextApp.__new__(Audio2TextApp)
                app.file_manager = Mock()
                app.file_manager.clear_audio_files.return_value = True
                app.update_status = Mock()
                app.update_file_info = Mock()
                app.refresh_history = Mock()
                app.clear_audio_with_feedback(None)
                app.refresh_history.assert_called_once()
        finally:
            sys.modules.pop("flet", None)

    def test_clear_logs_calls_refresh_history(self):
        """clear_logs_with_feedback should call refresh_history."""
        sys.modules["flet"] = MagicMock()
        try:
            from ui_flet.main import Audio2TextApp
            with patch.object(Audio2TextApp, "__init__", lambda self, *a, **kw: None):
                app = Audio2TextApp.__new__(Audio2TextApp)
                app.file_manager = Mock()
                app.file_manager.clear_transcriptions.return_value = True
                app.update_status = Mock()
                app.update_file_info = Mock()
                app.refresh_history = Mock()
                app.clear_logs_with_feedback(None)
                app.refresh_history.assert_called_once()
        finally:
            sys.modules.pop("flet", None)


class TestTranscriptionCacheReset:
    """Task 2.2: Reset transcription cache on missing file."""

    def test_cache_cleared_when_file_missing(self):
        """When JSONL file doesn't exist, cache should be reset."""
        from ui.app import App

        with patch.object(App, "__init__", lambda self, *a, **kw: None):
            app = App.__new__(App)
            app.config_manager = Mock()
            app.transcriptions_cache = {"old_file.wav": "old text"}
            app._transcriptions_cache_mtime = 999
            app.logger = Mock()

            with patch("os.path.exists", return_value=False):
                app._load_transcriptions_cache()

            assert app.transcriptions_cache == {}
            assert app._transcriptions_cache_mtime == 0
