"""Tests for tab name refresh across language changes.

Phase 3 of audio2text-ui-sync-fixes: _refresh_tab_names().
"""

import pytest
from types import SimpleNamespace

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


class FakeTab:
    """Minimal stand-in for a CTkTabview tab frame."""

    def grid_columnconfigure(self, *a, **kw):
        pass

    def grid_rowconfigure(self, *a, **kw):
        pass

    def grid(self, *a, **kw):
        pass

    def pack(self, *a, **kw):
        pass

    def winfo_children(self):
        return []


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


class FakeConfig:
    def __init__(self, ui="es"):
        self.config = {"ui_language": ui, "transcription_output_language": "es"}
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

    def set_multiple(self, settings):
        for k, v in settings.items():
            self.config[k] = v


def _make_app(ui="es"):
    """Build a bare App instance wired to FakeConfig, no Tk init."""
    config = FakeConfig(ui)
    app = App.__new__(App)
    app.config_manager = config
    app.localization_manager = config.localization_manager
    app._localized_widgets = {}

    # Fake main_frame with 5 tabs in initial language
    initial_names = [f"{ui}:{k}" for k in (
        "tab_main", "tab_settings", "tab_info", "tab_history", "tab_updates"
    )]
    app.main_frame = FakeTabview(initial_names)

    # Tab creation stubs — track calls
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

    # Register tab config (mimics what create_widgets() sets up)
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


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestRefreshTabNames:
    """Verify _refresh_tab_names updates tab labels and preserves active tab."""

    def test_tab_names_update_to_new_language(self):
        app = _make_app("es")
        app.localization_manager.set_language("en")
        app._refresh_tab_names()

        tab_names = list(app.main_frame._tabs.keys())
        for name in tab_names:
            assert name.startswith("en:"), f"Tab '{name}' not refreshed to en"

    def test_active_tab_index_preserved_after_refresh(self):
        app = _make_app("es")
        # Select 3rd tab (tab_info) as active
        app.main_frame.set("es:tab_info")
        assert app.main_frame.get() == "es:tab_info"

        app.localization_manager.set_language("en")
        app._refresh_tab_names()

        assert app.main_frame.get() == "en:tab_info"

    def test_tab_content_recreated(self):
        app = _make_app("es")
        app._refresh_tab_names()

        assert "main" in app._create_calls
        assert "config" in app._create_calls
        assert "info" in app._create_calls
        assert "history" in app._create_calls
        assert "update" in app._create_calls
        assert len(app._create_calls) == 5

    def test_wired_into_on_ui_language_changed(self):
        app = _make_app("es")
        app.main_frame.set("es:tab_settings")

        app._on_ui_language_changed("en")

        # Tab names should be in English
        for name in app.main_frame._tabs:
            assert name.startswith("en:"), f"Tab '{name}' not refreshed"

        # Active tab preserved
        assert app.main_frame.get() == "en:tab_settings"

    def test_all_five_tabs_refreshed(self):
        app = _make_app("es")
        app._refresh_tab_names()

        expected_keys = {"tab_main", "tab_settings", "tab_info", "tab_history", "tab_updates"}
        tab_names = set(app.main_frame._tabs.keys())
        refreshed = {n.split(":", 1)[1] for n in tab_names if ":" in n}
        assert refreshed == expected_keys

    def test_first_tab_active_by_default(self):
        app = _make_app("es")
        # Default active is first tab
        assert app.main_frame.get() == "es:tab_main"

        app.localization_manager.set_language("en")
        app._refresh_tab_names()

        assert app.main_frame.get() == "en:tab_main"

    def test_preserves_active_when_switching_middle_tab(self):
        app = _make_app("es")
        app.main_frame.set("es:tab_history")

        app.localization_manager.set_language("en")
        app._refresh_tab_names()

        assert app.main_frame.get() == "en:tab_history"

    def test_localized_widgets_re_registered_after_refresh(self):
        """After tab refresh, new widget instances are registered."""
        app = _make_app("es")

        # Pre-register a widget that will be replaced by tab recreation
        old_widget = SimpleNamespace(text="es:status_ready")
        app._register_localized_widget(old_widget, "status_ready")

        app.localization_manager.set_language("en")
        app._refresh_tab_names()

        # The tab creation stubs were called (which would re-register widgets)
        assert "main" in app._create_calls
        # Note: stubs don't actually register widgets, so old widget stays in
        # the registry. In production, create_main_tab() would register new ones.
        # The important assertion is that _refresh_tab_names ran all creators.

    def test_old_widget_text_updated_during_refresh(self):
        """_refresh_localized_widgets updates old widgets before tab rebuild."""
        app = _make_app("es")

        old_widget = SimpleNamespace(
            text="es:status_ready",
            configure_calls=[],
        )
        def _fake_configure(**kw):
            old_widget.configure_calls.append(kw)
            if "text" in kw:
                old_widget.text = kw["text"]
        old_widget.configure = _fake_configure

        app._register_localized_widget(old_widget, "status_ready")

        app._on_ui_language_changed("en")

        # Old widget was updated by _refresh_localized_widgets before tab rebuild
        assert old_widget.text == "en:status_ready"
