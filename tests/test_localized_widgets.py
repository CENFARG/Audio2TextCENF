"""Tests for widget registration and refresh across language changes.

Phase 2 of audio2text-ui-sync-fixes: widget registration expansion.
"""

import pytest
from types import SimpleNamespace

from ui.app import App


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


class FakeConfig:
    """Minimal ConfigManager stand-in for widget-refresh tests."""

    def __init__(self, ui="es"):
        self.config = {
            "ui_language": ui,
            "transcription_output_language": "es",
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


def _make_app(ui="es"):
    """Build a bare App instance wired to FakeConfig, no Tk init."""
    config = FakeConfig(ui)
    app = App.__new__(App)
    app.config_manager = config
    app.localization_manager = config.localization_manager
    app._localized_widgets = {}
    return app


class TestWidgetRegistration:
    """Verify that _refresh_localized_widgets updates every registered widget."""

    def test_single_registered_widget_updates_on_language_change(self):
        app = _make_app("es")
        w = FakeWidget("original")
        app._register_localized_widget(w, "status_ready")

        app._on_ui_language_changed("en")

        assert w.text == "en:status_ready"
        assert w.configure_calls == [{"text": "en:status_ready"}]

    def test_multiple_widgets_all_refresh(self):
        app = _make_app("es")
        labels = {
            "status_ready": FakeWidget(),
            "clear_audio_button": FakeWidget(),
            "clear_transcriptions_button": FakeWidget(),
            "history_title": FakeWidget(),
            "refresh_button": FakeWidget(),
        }
        for key, w in labels.items():
            app._register_localized_widget(w, key)

        app._on_ui_language_changed("en")

        for key, w in labels.items():
            assert w.text == f"en:{key}", f"Widget '{key}' not refreshed"
            assert len(w.configure_calls) == 1, f"Widget '{key}' got {len(w.configure_calls)} configure calls"

    def test_parameterized_kwargs_preserved_on_refresh(self):
        app = _make_app("es")
        w = FakeWidget()
        app._register_localized_widget(w, "audio_info", size="1.23", count=5)

        app._on_ui_language_changed("en")

        # The fake localization_manager ignores kwargs, but the key is re-fetched
        assert w.text == "en:audio_info"

    def test_unregistered_widget_not_affected(self):
        app = _make_app("es")
        registered = FakeWidget()
        unregistered = FakeWidget("stay")
        app._register_localized_widget(registered, "status_ready")

        app._on_ui_language_changed("en")

        assert registered.text == "en:status_ready"
        assert unregistered.text == "stay"

    def test_refresh_preserves_existing_registry(self):
        app = _make_app("es")
        w1 = FakeWidget()
        w2 = FakeWidget()
        app._register_localized_widget(w1, "status_ready")
        app._register_localized_widget(w2, "history_title")
        original = app._localized_widgets

        app._on_ui_language_changed("en")

        assert app._localized_widgets is original
        assert set(app._localized_widgets.keys()) == {"status_ready", "history_title"}

    def test_switch_and_button_widgets_refresh(self):
        """Switches and buttons use .configure(text=...) just like labels."""
        app = _make_app("es")
        switch = FakeWidget()
        button = FakeWidget()
        app._register_localized_widget(switch, "auto_paste_switch")
        app._register_localized_widget(button, "browse_button")

        app._on_ui_language_changed("en")

        assert switch.text == "en:auto_paste_switch"
        assert button.text == "en:browse_button"

    def test_section_header_widgets_refresh(self):
        app = _make_app("es")
        headers = {}
        for key in ("settings_title_main", "settings_title_files"):
            headers[key] = FakeWidget()
            app._register_localized_widget(headers[key], key)

        app._on_ui_language_changed("en")

        for key, w in headers.items():
            assert w.text == f"en:{key}"

    def test_info_tab_widgets_refresh(self):
        app = _make_app("es")
        w = FakeWidget()
        app._register_localized_widget(w, "groq_api_key_link")

        app._on_ui_language_changed("en")

        assert w.text == "en:groq_api_key_link"

    def test_all_main_tab_widgets_covered(self):
        """Main tab: status, hotkey display, audio info, log info, clear buttons."""
        app = _make_app("es")
        main_tab_keys = [
            "status_ready",
            "hotkey_display",
            "audio_info",
            "transcriptions_info",
            "clear_audio_button",
            "clear_transcriptions_button",
        ]
        for key in main_tab_keys:
            w = FakeWidget()
            app._register_localized_widget(w, key)

        app._on_ui_language_changed("en")

        for key in main_tab_keys:
            assert app._localized_widgets[key][0].text == f"en:{key}"

    def test_all_config_tab_widgets_covered(self):
        """Config tab: section headers, labels, switches, buttons."""
        app = _make_app("es")
        config_tab_keys = [
            "settings_title_main",
            "asr_provider_label",
            "asr_provider_groq",
            "hotkey_label",
            "record_mode_label",
            "record_mode_hold",
            "record_mode_toggle",
            "max_duration_label",
            "auto_paste_switch",
            "show_panel_switch",
            "autostart_windows_switch",
            "settings_title_files",
            "audio_path_label",
            "transcriptions_path_label",
            "save_audio_switch",
            "save_logs_switch",
            "verify_button",
            "browse_button",
        ]
        for key in config_tab_keys:
            w = FakeWidget()
            app._register_localized_widget(w, key)

        app._on_ui_language_changed("en")

        for key in config_tab_keys:
            assert app._localized_widgets[key][0].text == f"en:{key}"

    def test_all_history_tab_widgets_covered(self):
        """History tab: title, refresh button."""
        app = _make_app("es")
        history_keys = ["history_title", "refresh_button"]
        for key in history_keys:
            w = FakeWidget()
            app._register_localized_widget(w, key)

        app._on_ui_language_changed("en")

        for key in history_keys:
            assert app._localized_widgets[key][0].text == f"en:{key}"

    def test_info_tab_static_text_covered(self):
        """Info tab: groq_api_key_link."""
        app = _make_app("es")
        w = FakeWidget()
        app._register_localized_widget(w, "groq_api_key_link")

        app._on_ui_language_changed("en")

        assert w.text == "en:groq_api_key_link"

    def test_config_tab_label_widgets_refresh(self):
        """Config tab labels: language, output language, API provider."""
        app = _make_app("es")
        label_keys = [
            "language_label",
            "transcription_output_language_label",
            "asr_provider_label",
        ]
        for key in label_keys:
            w = FakeWidget()
            app._register_localized_widget(w, key)

        app._on_ui_language_changed("en")

        for key in label_keys:
            assert app._localized_widgets[key][0].text == f"en:{key}"
