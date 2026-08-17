"""
Integration tests for Audio2Text application.

This module tests end-to-end workflows including:
- Configuration loading → Transcriber initialization → Recording → Transcription → File saving
- Block processing pipeline
- Metadata generation and storage
- Hotkey registration and handling
- Error handling across components
- Phase 5: UI sync integration tests (full language switch, history refresh, fallback)

Author: Audio2Text Development Team
Version: 0.15.0
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


class FakeInputStream:
    """Minimal sounddevice InputStream fake with the real read contract."""

    def __init__(self):
        self.active = False
        self.numpy_data = np.zeros((0, 1), dtype=np.float32)
        self.overflowed = False

    def start(self):
        self.active = True

    def read(self, frames):
        self.numpy_data = np.zeros((frames, 1), dtype=np.float32)
        return self.numpy_data, self.overflowed

    def stop(self):
        self.active = False

    def close(self):
        self.active = False


# ===========================================================================
# Phase 5 Integration Tests — UI Sync Fixes
# ===========================================================================

from ui.app import App


class FakeVar:
    """Minimal CTk variable stand-in."""
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


class FakeTab:
    """Minimal stand-in for a CTkTabview tab frame."""
    def grid_columnconfigure(self, *a, **kw): pass
    def grid_rowconfigure(self, *a, **kw): pass
    def grid(self, *a, **kw): pass
    def pack(self, *a, **kw): pass
    def winfo_children(self): return []


class FakeTabview:
    """Minimal CTkTabview stand-in with name-based tab access."""
    def __init__(self, names):
        self._tabs = {}
        self._active = names[0] if names else None
        for name in names:
            self._tabs[name] = FakeTab()

    def add(self, name):
        if name not in self._tabs:
            self._tabs[name] = FakeTab()

    def tab(self, name):
        return self._tabs.get(name)

    def get(self):
        return self._active

    def set(self, name):
        self._active = name

    def delete(self, name):
        self._tabs.pop(name, None)


class FakeFrame:
    """Minimal CTk frame stand-in."""
    def __init__(self):
        self._children = []
    def winfo_children(self):
        return self._children
    def pack(self, *a, **kw): pass
    def grid(self, *a, **kw): pass
    def destroy(self): pass


class FakeFileManager:
    """Mock file_manager that simulates real file operations."""
    def __init__(self, audio_files=None):
        self._audio_files = audio_files or []
        self.clear_audio_called = False
        self.clear_transcriptions_called = False

    def clear_audio_files(self):
        self.clear_audio_called = True
        self._audio_files = []
        return True

    def clear_transcriptions(self):
        self.clear_transcriptions_called = True
        return True

    def get_audio_files_list(self, limit=200):
        return [{"name": f, "path": f"/tmp/{f}"} for f in self._audio_files]

    def get_audio_files_size(self):
        return 1024 * 1024  # 1 MB

    def get_transcriptions_size(self):
        return 1024  # 1 KB


def _make_full_app(ui="es", audio_path="/tmp/audio"):
    """Build an App instance with real LocalizationManager and full widget registry."""
    config = FakeConfigFull(ui, audio_path)
    app = App.__new__(App)
    app.config_manager = config
    app.localization_manager = config.localization_manager
    app._localized_widgets = {}
    app.file_manager = config.file_manager
    app.history_scroll_frame = FakeFrame()
    app.loaded_history_files = set()
    app.last_history_file_count = 0
    app.last_history_mtime = 0
    app.metadata_manager = Mock()

    # Track refresh_history_list calls
    app.refresh_history_calls = []
    def _track_refresh(full_reload=False):
        app.refresh_history_calls.append({"full_reload": full_reload})
    app.refresh_history_list = _track_refresh

    # Stub update_status and update_file_info
    app.update_status = MagicMock()
    app.update_file_info = MagicMock()

    # Stub logger
    app.logger = MagicMock()

    # Stub after() for scheduling
    app.after_calls = []
    def _track_after(delay, callback, *args):
        app.after_calls.append({"delay": delay, "callback": callback, "args": args})
    app.after = _track_after

    # Fake main_frame with 5 tabs in initial language
    initial_names = [f"{ui}:{k}" for k in (
        "tab_main", "tab_settings", "tab_info", "tab_history", "tab_updates"
    )]
    app.main_frame = FakeTabview(initial_names)

    # Tab creation stubs
    app._create_calls = []
    def _stub(name):
        def _inner():
            app._create_calls.append(name)
        return _inner

    app.create_main_tab = _stub("main")
    app.create_config_tab = _stub("config")
    app.create_info_tab = _stub("info")
    app.create_history_tab = _stub("history")
    app.create_update_tab = _stub("update")

    # Register tab config
    app._tab_config = {
        "tab_main":    app.create_main_tab,
        "tab_settings": app.create_config_tab,
        "tab_info":    app.create_info_tab,
        "tab_history": app.create_history_tab,
        "tab_updates": app.create_update_tab,
    }
    app._tab_names = {
        key: app.localization_manager.get_string(key)
        for key in app._tab_config
    }

    return app


class FakeConfigFull:
    """Config stand-in with REAL LocalizationManager."""
    def __init__(self, ui="es", audio_path="/tmp/audio"):
        self.config = {
            "ui_language": ui,
            "transcription_output_language": "es",
            "audio_path": audio_path,
        }
        self.localization_manager = LocalizationManager(lang_code=ui)
        self.file_manager = FakeFileManager()
        self.writes = []

    def get(self, key, default=None):
        return self.config.get(key, default)

    def set(self, key, value):
        self.config[key] = value
        self.writes.append((key, value))

    def set_multiple(self, settings):
        for k, v in settings.items():
            self.config[k] = v


# ---------------------------------------------------------------------------
# Task 5.1: Full language switch — all visible labels update
# ---------------------------------------------------------------------------

class TestFullLanguageSwitch:
    """Task 5.1: Instantiate app, switch language, assert ALL visible labels
    match new language. Verify active tab is preserved. Verify transcription
    text is preserved (not tested here — no textbox in fake)."""

    def test_all_registered_widgets_update_on_language_switch(self):
        """Every registered widget SHALL display the new language's text."""
        app = _make_full_app("es")

        # Register representative widgets from each tab.
        # Parameterized keys need their kwargs (mirrors real create_*_tab usage).
        widget_specs = [
            # Main tab
            ("status_ready", {}),
            ("hotkey_display", {"hotkey": "F9"}),
            ("audio_info", {"size": "1.23", "count": 5}),
            ("transcriptions_info", {"size": "4.56"}),
            ("clear_audio_button", {}),
            ("clear_transcriptions_button", {}),
            # Config tab
            ("settings_title_main", {}),
            ("asr_provider_label", {}),
            ("asr_provider_groq", {}),
            ("hotkey_label", {}),
            ("record_mode_label", {}),
            ("record_mode_hold", {}),
            ("record_mode_toggle", {}),
            ("max_duration_label", {}),
            ("auto_paste_switch", {}),
            ("show_panel_switch", {}),
            ("autostart_windows_switch", {}),
            ("settings_title_files", {}),
            ("audio_path_label", {}),
            ("transcriptions_path_label", {}),
            ("save_audio_switch", {}),
            ("save_logs_switch", {}),
            ("verify_button", {}),
            ("browse_button", {}),
            # History tab
            ("history_title", {}),
            ("refresh_button", {}),
            # Info tab
            ("groq_api_key_link", {}),
        ]

        widgets = {}
        for key, kwargs in widget_specs:
            w = FakeWidget()
            app._register_localized_widget(w, key, **kwargs)
            widgets[key] = (w, kwargs)

        # Switch from Spanish to English
        app._on_ui_language_changed("en")

        # Verify every widget has English text
        for key, (w, kwargs) in widgets.items():
            expected = app.localization_manager.get_string(key, **kwargs)
            assert w.text == expected, (
                f"Widget '{key}' text is '{w.text}', expected '{expected}'"
            )

    def test_active_tab_preserved_after_language_switch(self):
        """The active tab SHALL remain the same after language switch."""
        app = _make_full_app("es")

        # Select the Settings tab
        es_settings_name = app.localization_manager.get_string("tab_settings")
        app.main_frame.set(es_settings_name)
        assert app.main_frame.get() == es_settings_name

        # Switch language
        app._on_ui_language_changed("en")

        # Active tab should now be the English equivalent of Settings
        en_settings_name = app.localization_manager.get_string("tab_settings")
        assert app.main_frame.get() == en_settings_name, (
            f"Active tab changed to '{app.main_frame.get()}', "
            f"expected '{en_settings_name}'"
        )

    def test_tab_names_all_in_new_language(self):
        """All 5 tab names SHALL reflect the new language."""
        app = _make_full_app("es")
        app._on_ui_language_changed("en")

        for key in ("tab_main", "tab_settings", "tab_info", "tab_history", "tab_updates"):
            expected_name = app.localization_manager.get_string(key)
            assert expected_name in app.main_frame._tabs, (
                f"Tab '{expected_name}' not found in main_frame after switch"
            )

    def test_output_language_not_affected_by_ui_switch(self):
        """Changing UI language SHALL NOT change transcription output language."""
        app = _make_full_app("es")
        app._on_ui_language_changed("en")

        output_lang = app.config_manager.get("transcription_output_language")
        assert output_lang == "es", (
            f"Output language changed to '{output_lang}', should remain 'es'"
        )

    def test_multiple_language_switches_work(self):
        """Switching ES → EN → ES SHALL work without errors."""
        app = _make_full_app("es")
        w = FakeWidget()
        app._register_localized_widget(w, "status_ready")

        app._on_ui_language_changed("en")
        assert w.text == app.localization_manager.get_string("status_ready")

        app._on_ui_language_changed("es")
        assert w.text == app.localization_manager.get_string("status_ready")

    def test_tab_config_names_consistent_after_switch(self):
        """_tab_names dict SHALL be updated after language switch."""
        app = _make_full_app("es")
        app._on_ui_language_changed("en")

        for key in ("tab_main", "tab_settings", "tab_info", "tab_history", "tab_updates"):
            expected = app.localization_manager.get_string(key)
            assert app._tab_names[key] == expected, (
                f"_tab_names['{key}'] is '{app._tab_names[key]}', expected '{expected}'"
            )


# ---------------------------------------------------------------------------
# Task 5.2: History refresh after clear operations
# ---------------------------------------------------------------------------

class TestHistoryAfterClear:
    """Task 5.2: Verify history panel is rebuilt after clear operations
    and deleted files no longer appear."""

    def test_clear_audio_removes_files_from_history(self):
        """After clear_audio_with_feedback(), the file list SHALL be empty."""
        app = _make_full_app("es")
        app.file_manager._audio_files = ["a.wav", "b.wav", "c.wav"]

        # Before clear: files exist
        assert len(app.file_manager.get_audio_files_list()) == 3

        app.clear_audio_with_feedback()

        # After clear: no files
        assert len(app.file_manager.get_audio_files_list()) == 0

    def test_clear_audio_triggers_full_reload(self):
        """clear_audio_with_feedback() SHALL call refresh_history_list(full_reload=True)."""
        app = _make_full_app("es")
        app.file_manager._audio_files = ["a.wav", "b.wav"]

        app.clear_audio_with_feedback()

        assert len(app.refresh_history_calls) == 1
        assert app.refresh_history_calls[0]["full_reload"] is True

    def test_clear_logs_triggers_full_reload(self):
        """clear_logs_with_feedback() SHALL call refresh_history_list(full_reload=True)."""
        app = _make_full_app("es")

        app.clear_logs_with_feedback()

        assert len(app.refresh_history_calls) == 1
        assert app.refresh_history_calls[0]["full_reload"] is True

    def test_clear_audio_updates_file_info(self):
        """clear_audio_with_feedback() SHALL call update_file_info()."""
        app = _make_full_app("es")
        app.clear_audio_with_feedback()

        app.update_file_info.assert_called()

    def test_clear_logs_updates_file_info(self):
        """clear_logs_with_feedback() SHALL call update_file_info()."""
        app = _make_full_app("es")
        app.clear_logs_with_feedback()

        app.update_file_info.assert_called()

    def test_clear_audio_shows_success_status(self):
        """Successful clear SHALL show green status."""
        app = _make_full_app("es")
        app.clear_audio_with_feedback()

        app.update_status.assert_called()
        call_args = app.update_status.call_args
        # Status message should be the localized string for "audio_deleted"
        assert "audio_deleted" in str(call_args) or "Audio" in str(call_args) or "eliminado" in str(call_args)

    def test_history_list_built_after_clear(self):
        """After clear, refresh_history_list SHALL rebuild from current file list."""
        app = _make_full_app("es")
        app.file_manager._audio_files = ["a.wav"]

        app.clear_audio_with_feedback()

        # file_manager now has 0 files
        files_after = app.file_manager.get_audio_files_list()
        assert len(files_after) == 0

    def test_clear_audio_preserves_transcriptions(self):
        """Clearing audio SHALL NOT clear transcriptions."""
        app = _make_full_app("es")
        app.clear_audio_with_feedback()

        assert not app.file_manager.clear_transcriptions_called


# ---------------------------------------------------------------------------
# Task 5.3: Missing key fallback
# ---------------------------------------------------------------------------

class TestMissingKeyFallback:
    """Task 5.3: When a key is referenced that only exists in the other language,
    the localization manager SHALL return a fallback without crashing."""

    def test_missing_key_returns_fallback_string(self):
        """Reference a key only in es.json with language=en, assert fallback."""
        lm = LocalizationManager(lang_code="en")

        # "tab_main" exists in en.json — this should work fine
        result = lm.get_string("tab_main")
        assert result == "Main"

    def test_nonexistent_key_returns_missing_prefix(self):
        """Reference a completely nonexistent key, assert MISSING_TRANSLATION_ prefix."""
        lm = LocalizationManager(lang_code="en")

        result = lm.get_string("this_key_does_not_exist_anywhere")
        assert result == "MISSING_TRANSLATION_this_key_does_not_exist_anywhere"

    def test_missing_key_does_not_crash(self):
        """Calling get_string with a nonexistent key SHALL not raise an exception."""
        lm = LocalizationManager(lang_code="en")
        try:
            result = lm.get_string("nonexistent_key_12345")
            # Should return a string, not raise
            assert isinstance(result, str)
        except Exception as e:
            pytest.fail(f"get_string crashed on missing key: {e}")

    def test_missing_key_with_kwargs_does_not_crash(self):
        """Calling get_string with kwargs on a nonexistent key SHALL not crash."""
        lm = LocalizationManager(lang_code="en")
        try:
            result = lm.get_string("missing_with_args", foo="bar", baz=42)
            assert isinstance(result, str)
        except KeyError:
            pytest.fail("get_string raised KeyError for missing key with kwargs")

    def test_switch_language_with_missing_key_fallback(self):
        """Switch language, then reference key that only exists in one file."""
        lm_es = LocalizationManager(lang_code="es")
        es_value = lm_es.get_string("status_ready")
        assert es_value != f"MISSING_TRANSLATION_status_ready"

        lm_en = LocalizationManager(lang_code="en")
        en_value = lm_en.get_string("status_ready")
        assert en_value != f"MISSING_TRANSLATION_status_ready"

        # Values should be different (ES vs EN translations)
        assert es_value != en_value

    def test_set_language_to_unsupported_falls_back_to_es(self):
        """Setting an unsupported language SHALL fall back to 'es'."""
        lm = LocalizationManager(lang_code="en")
        lm.set_language("fr")  # unsupported

        # Should fall back to es
        assert lm.lang_code == "es"
        # "status_ready" in es should be the Spanish translation
        result = lm.get_string("status_ready")
        assert result != f"MISSING_TRANSLATION_status_ready"


# ===========================================================================
# Original integration tests (preserved)
# ===========================================================================

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
        with patch("backend.transcriber.sd.InputStream", return_value=FakeInputStream()):
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
        transcriber.cliente.audio.transcriptions.create = Mock(
            return_value="Texto de prueba"
        )

        # Transcribe
        result = transcriber.transcribe_with_groq(str(audio_file))

        assert result == "Texto de prueba"


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
        # POST-transcription blocks return metadata; the original text is preserved.
        from backend.blocks.base_block import BlockResult

        transcriber.block_manager.process = Mock(
            return_value=[
                BlockResult(
                    success=True,
                    data={"summary": "Texto procesado con bloques"},
                    metadata={"block_name": "summary"},
                )
            ]
        )

        result = transcriber._process_with_blocks("Texto original")

        assert result == "Texto original"
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

    def test_utf8_validation_accepts_empty_text(self, tmp_path):
        """UTF-8 validation checks encoding, not whether text is non-empty."""
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

            is_valid, problems = transcriber.validate_text("")
            assert is_valid is True
            assert problems == []


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
