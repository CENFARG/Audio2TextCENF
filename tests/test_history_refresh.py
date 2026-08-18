"""Tests for history auto-refresh after clear operations.

Phase 4 of audio2text-ui-sync-fixes: clear triggers refresh, deletion detection.
"""

import pytest
import os
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from ui.app import App


# ---------------------------------------------------------------------------
# Fakes
# ---------------------------------------------------------------------------

class FakeVar:
    def __init__(self, value=""):
        self._value = value
    def get(self):
        return self._value
    def set(self, value):
        self._value = value


class FakeWidget:
    """Minimal CTk widget stand-in that records configure() calls."""
    def __init__(self, initial_text=""):
        self.text = initial_text
        self.configure_calls = []

    def configure(self, **kwargs):
        self.configure_calls.append(kwargs)
        if "text" in kwargs:
            self.text = kwargs["text"]


class FakeFrame:
    """Minimal CTk frame stand-in."""
    def winfo_children(self):
        return []
    def pack(self, *a, **kw):
        pass
    def grid(self, *a, **kw):
        pass
    def destroy(self):
        pass


class FakeConfig:
    def __init__(self, ui="es", audio_path="/tmp/audio"):
        self.config = {
            "ui_language": ui,
            "transcription_output_language": "es",
            "audio_path": audio_path,
        }
        self.localization_manager = SimpleNamespace(
            lang_code=ui,
            set_language=lambda value: setattr(
                self.localization_manager, "lang_code", value
            ),
            get_string=lambda key, **kwargs: f"{self.localization_manager.lang_code}:{key}",
        )
        self.writes = []

    def get(self, key, default=None):
        return self.config.get(key, default)

    def set(self, key, value):
        self.config[key] = value
        self.writes.append((key, value))


class FakeFileManager:
    """Mock file_manager that tracks clear calls."""
    def __init__(self):
        self.clear_audio_called = False
        self.clear_transcriptions_called = False

    def clear_audio_files(self):
        self.clear_audio_called = True
        return True

    def clear_transcriptions(self):
        self.clear_transcriptions_called = True
        return True

    def get_audio_files_list(self, limit=200):
        return []


def _make_app(ui="es", audio_path="/tmp/audio"):
    """Build a bare App instance wired to FakeConfig, no Tk init."""
    config = FakeConfig(ui, audio_path)
    app = App.__new__(App)
    app.config_manager = config
    app.localization_manager = config.localization_manager
    app._localized_widgets = {}
    app.file_manager = FakeFileManager()
    app.history_scroll_frame = FakeFrame()
    app.loaded_history_files = set()
    app.last_history_file_count = 0
    app.last_history_mtime = 0

    # Track refresh_history_list calls
    app.refresh_history_calls = []
    app._original_refresh = app.refresh_history_list if hasattr(app, 'refresh_history_list') else None

    def _track_refresh(full_reload=False):
        app.refresh_history_calls.append({"full_reload": full_reload})

    app.refresh_history_list = _track_refresh

    # Stub update_status and update_file_info (called by clear methods)
    app.update_status = MagicMock()
    app.update_file_info = MagicMock()

    # Stub logger
    app.logger = MagicMock()

    # Stub after() for auto_refresh_history scheduling
    app.after_calls = []
    def _track_after(delay, callback, *args):
        app.after_calls.append({"delay": delay, "callback": callback, "args": args})
    app.after = _track_after

    # Stub main_frame for auto_refresh_history
    app.main_frame = SimpleNamespace(
        get=lambda: f"{ui}:tab_history"
    )

    return app


# ---------------------------------------------------------------------------
# Tests: Clear operations trigger history refresh
# ---------------------------------------------------------------------------

class TestClearRefreshesHistory:
    """Verify clear_audio and clear_logs call refresh_history_list(full_reload=True)."""

    def test_clear_audio_calls_refresh_history(self):
        """Task 4.1: clear_audio_with_feedback() must call refresh_history_list(full_reload=True)."""
        app = _make_app()
        app.clear_audio_with_feedback()

        assert len(app.refresh_history_calls) == 1, (
            f"Expected 1 refresh call, got {len(app.refresh_history_calls)}"
        )
        assert app.refresh_history_calls[0]["full_reload"] is True, (
            "refresh_history_list must be called with full_reload=True after clear audio"
        )

    def test_clear_logs_calls_refresh_history(self):
        """Task 4.1: clear_logs_with_feedback() must call refresh_history_list(full_reload=True)."""
        app = _make_app()
        app.clear_logs_with_feedback()

        assert len(app.refresh_history_calls) == 1, (
            f"Expected 1 refresh call, got {len(app.refresh_history_calls)}"
        )
        assert app.refresh_history_calls[0]["full_reload"] is True, (
            "refresh_history_list must be called with full_reload=True after clear logs"
        )

    def test_clear_audio_still_updates_file_info(self):
        """Ensure update_file_info is still called (existing behavior preserved)."""
        app = _make_app()
        app.clear_audio_with_feedback()

        app.update_file_info.assert_called_once()

    def test_clear_logs_still_updates_file_info(self):
        """Ensure update_file_info is still called (existing behavior preserved)."""
        app = _make_app()
        app.clear_logs_with_feedback()

        app.update_file_info.assert_called_once()

    def test_clear_audio_success_updates_status_green(self):
        """Successful clear shows green status."""
        app = _make_app()
        app.clear_audio_with_feedback()

        app.update_status.assert_called_once()
        call_args = app.update_status.call_args
        assert call_args[0][1] == "green" or call_args[1].get("color") == "green"

    def test_clear_audio_failure_updates_status_red(self):
        """Failed clear shows red status."""
        app = _make_app()
        app.file_manager.clear_audio_files = MagicMock(return_value=False)
        app.clear_audio_with_feedback()

        app.update_status.assert_called_once()
        call_args = app.update_status.call_args
        assert call_args[0][1] == "red" or call_args[1].get("color") == "red"


# ---------------------------------------------------------------------------
# Tests: Auto-refresh detects deletions
# ---------------------------------------------------------------------------

class TestAutoRefreshDetectsDeletions:
    """Verify auto_refresh_history detects both increases AND decreases."""

    def test_detects_file_count_decrease(self):
        """Task 4.3: When file count decreases, auto_refresh must trigger full_reload."""
        app = _make_app()
        # Pretend we previously had 5 files
        app.last_history_file_count = 5
        app.last_history_mtime = 1000.0

        # Now only 3 files exist
        with patch("os.path.exists", return_value=True), \
             patch("os.listdir", return_value=["a.wav", "b.wav", "c.wav"]), \
             patch("os.path.getmtime", return_value=500.0):
            app.auto_refresh_history()

        # Should have triggered a full_reload because count decreased
        full_reload_calls = [c for c in app.refresh_history_calls if c["full_reload"]]
        assert len(full_reload_calls) == 1, (
            "auto_refresh_history must call refresh_history_list(full_reload=True) on count decrease"
        )

    def test_detects_mtime_decrease(self):
        """Task 4.3: When mtime decreases (file deleted), auto_refresh must trigger full_reload."""
        app = _make_app()
        app.last_history_file_count = 3
        app.last_history_mtime = 2000.0

        # Same count but earlier mtime (a file was deleted)
        with patch("os.path.exists", return_value=True), \
             patch("os.listdir", return_value=["a.wav", "b.wav", "c.wav"]), \
             patch("os.path.getmtime", return_value=1000.0):
            app.auto_refresh_history()

        full_reload_calls = [c for c in app.refresh_history_calls if c["full_reload"]]
        assert len(full_reload_calls) == 1, (
            "auto_refresh_history must call refresh_history_list(full_reload=True) on mtime decrease"
        )

    def test_detects_file_count_increase(self):
        """Existing behavior: file count increase triggers refresh (full_reload=False)."""
        app = _make_app()
        app.last_history_file_count = 2
        app.last_history_mtime = 1000.0

        with patch("os.path.exists", return_value=True), \
             patch("os.listdir", return_value=["a.wav", "b.wav", "c.wav"]), \
             patch("os.path.getmtime", return_value=1500.0):
            app.auto_refresh_history()

        # Count increased → refresh with full_reload=False (existing behavior)
        assert len(app.refresh_history_calls) == 1
        assert app.refresh_history_calls[0]["full_reload"] is False

    def test_no_refresh_when_no_change(self):
        """No change means no refresh."""
        app = _make_app()
        app.last_history_file_count = 3
        app.last_history_mtime = 1000.0

        with patch("os.path.exists", return_value=True), \
             patch("os.listdir", return_value=["a.wav", "b.wav", "c.wav"]), \
             patch("os.path.getmtime", return_value=1000.0):
            app.auto_refresh_history()

        assert len(app.refresh_history_calls) == 0, (
            "auto_refresh_history should not refresh when nothing changed"
        )

    def test_reschedules_after_check(self):
        """auto_refresh_history must re-schedule itself via after()."""
        app = _make_app()
        app.last_history_file_count = 0
        app.last_history_mtime = 0

        with patch("os.path.exists", return_value=False):
            app.auto_refresh_history()

        # Should have scheduled next check
        assert len(app.after_calls) >= 1
        # The scheduled callback should be auto_refresh_history itself
        assert any(
            c["callback"] == app.auto_refresh_history for c in app.after_calls
        ), "auto_refresh_history must re-schedule itself"

    def test_only_refreshes_on_history_tab(self):
        """No refresh if current tab is not the history tab."""
        app = _make_app()
        app.main_frame.get = lambda: "es:tab_main"
        app.last_history_file_count = 0
        app.last_history_mtime = 0

        with patch("os.path.exists", return_value=True), \
             patch("os.listdir", return_value=["a.wav"]), \
             patch("os.path.getmtime", return_value=100.0):
            app.auto_refresh_history()

        assert len(app.refresh_history_calls) == 0, (
            "auto_refresh_history must not refresh when not on history tab"
        )

    def test_updates_cached_values_after_refresh(self):
        """After refresh, cached count/mtime must be updated."""
        app = _make_app()
        app.last_history_file_count = 2
        app.last_history_mtime = 1000.0

        with patch("os.path.exists", return_value=True), \
             patch("os.listdir", return_value=["a.wav", "b.wav", "c.wav"]), \
             patch("os.path.getmtime", return_value=1500.0):
            app.auto_refresh_history()

        assert app.last_history_file_count == 3
        assert app.last_history_mtime == 1500.0
