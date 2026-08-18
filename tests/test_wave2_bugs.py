"""Tests for Wave 2 bugfixes: _reregister_hotkey delegation, _delete_audio_file full_reload."""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestReregisterHotkey:
    """Task 1.2: _reregister_hotkey should delegate to transcriber.update_hotkey."""

    def test_reregister_hotkey_calls_transcriber_update_hotkey(self):
        """_reregister_hotkey(new_hotkey) MUST call self.transcriber.update_hotkey(new_hotkey)."""
        from ui.app import App

        with patch.object(App, "__init__", lambda self, *a, **kw: None):
            app = App.__new__(App)
            app.transcriber = Mock()
            app.logger = Mock()

            app._reregister_hotkey("ctrl+f9")

            app.transcriber.update_hotkey.assert_called_once_with("ctrl+f9")

    def test_reregister_hotkey_does_not_call_keyboard_unhook_all(self):
        """_reregister_hotkey must NOT call keyboard.unhook_all (which nukes all hooks)."""
        from ui.app import App

        with patch.object(App, "__init__", lambda self, *a, **kw: None):
            app = App.__new__(App)
            app.transcriber = Mock()
            app.logger = Mock()

            with patch("ui.app.keyboard", create=True) as mock_keyboard:
                app._reregister_hotkey("f12")
                mock_keyboard.unhook_all.assert_not_called()

    def test_reregister_hotkey_logs_error_on_exception(self):
        """_reregister_hotkey should log error if transcriber.update_hotkey raises."""
        from ui.app import App

        with patch.object(App, "__init__", lambda self, *a, **kw: None):
            app = App.__new__(App)
            app.transcriber = Mock()
            app.transcriber.update_hotkey.side_effect = RuntimeError("boom")
            app.logger = Mock()

            # Should not raise
            app._reregister_hotkey("f12")

            app.logger.error.assert_called_once()


class TestDeleteAudioFileFullReload:
    """Task 2.3: _delete_audio_file should call refresh_history_list(full_reload=True)."""

    def test_delete_audio_file_calls_refresh_with_full_reload(self):
        """_delete_audio_file MUST call refresh_history_list(full_reload=True) after os.remove."""
        from ui.app import App

        with patch.object(App, "__init__", lambda self, *a, **kw: None):
            app = App.__new__(App)
            app.localization_manager = Mock()
            app.localization_manager.get_string.return_value = "Confirm"
            app.refresh_history_list = Mock()
            app.update_file_info = Mock()

            with patch("ui.app.messagebox") as mock_mb, \
                 patch("ui.app.os.remove") as mock_remove:
                mock_mb.askyesno.return_value = True

                app._delete_audio_file("/fake/audio.wav")

                mock_remove.assert_called_once_with("/fake/audio.wav")
                app.refresh_history_list.assert_called_once_with(full_reload=True)
                app.update_file_info.assert_called_once()

    def test_delete_audio_file_no_refresh_on_cancel(self):
        """_delete_audio_file should NOT call refresh_history_list if user cancels."""
        from ui.app import App

        with patch.object(App, "__init__", lambda self, *a, **kw: None):
            app = App.__new__(App)
            app.localization_manager = Mock()
            app.localization_manager.get_string.return_value = "Confirm"
            app.refresh_history_list = Mock()
            app.update_file_info = Mock()

            with patch("ui.app.messagebox") as mock_mb:
                mock_mb.askyesno.return_value = False

                app._delete_audio_file("/fake/audio.wav")

                app.refresh_history_list.assert_not_called()
                app.update_file_info.assert_not_called()
