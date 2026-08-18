import json
from types import SimpleNamespace

import pytest

from backend.localization_manager import LocalizationManager
from ui.app import App


class FakeVar:
    def __init__(self, value):
        self.value = value

    def get(self):
        return self.value

    def set(self, value):
        self.value = value


class FakeWidget:
    def __init__(self):
        self.configured = []

    def configure(self, **kwargs):
        self.configured.append(kwargs)


class FakeConfig:
    def __init__(self, ui="es", output="es"):
        self.config = {
            "ui_language": ui,
            "transcription_output_language": output,
            "default_language": "es",
        }
        self.localization_manager = SimpleNamespace(
            lang_code=ui,
            set_language=lambda value: setattr(self.localization_manager, "lang_code", value),
            get_string=lambda key, **kwargs: f"{self.localization_manager.lang_code}:{key}",
        )
        self.writes = []

    def get(self, key, default=None):
        return self.config.get(key, default)

    def set(self, key, value):
        self.config[key] = value
        self.writes.append((key, value))


@pytest.mark.parametrize("ui_language,output_language", [(ui, output) for ui in ("es", "en") for output in ("es", "en")])
def test_all_language_combinations_are_independent(ui_language, output_language):
    config = FakeConfig(ui_language, output_language)
    app = App.__new__(App)
    app.config_manager = config
    app.localization_manager = config.localization_manager
    app._localized_widgets = {}

    app._on_output_language_changed(output_language)

    assert config.get("transcription_output_language") == output_language
    assert config.get("ui_language") == ui_language


def test_ui_language_refreshes_registered_labels_in_place_without_recreating_ui():
    config = FakeConfig()
    app = App.__new__(App)
    app.config_manager = config
    app.localization_manager = config.localization_manager
    app._localized_widgets = {"language_label": (FakeWidget(), {})}
    original_widgets = app._localized_widgets

    app._on_ui_language_changed("en")

    assert app._localized_widgets is original_widgets
    assert config.get("ui_language") == "en"
    assert config.get("transcription_output_language") == "es"
    assert original_widgets["language_label"][0].configured == [{"text": "en:language_label"}]


def test_output_language_change_does_not_relabel_ui_or_write_ui_setting():
    config = FakeConfig(ui="en", output="es")
    app = App.__new__(App)
    app.config_manager = config
    app.localization_manager = config.localization_manager
    app._localized_widgets = {"language_label": (FakeWidget(), {})}

    app._on_output_language_changed("en")

    assert config.get("transcription_output_language") == "en"
    assert config.get("ui_language") == "en"
    assert config.localization_manager.lang_code == "en"
    assert config.writes == [("transcription_output_language", "en")]


def test_localization_manager_accepts_only_supported_languages(tmp_path):
    (tmp_path / "es.json").write_text(json.dumps({"language_label": "Idioma"}), encoding="utf-8")
    (tmp_path / "en.json").write_text(json.dumps({"language_label": "Language"}), encoding="utf-8")
    manager = LocalizationManager(lang_code="fr", lang_dir=str(tmp_path))

    assert manager.lang_code == "es"
    assert manager.set_language("fr") == "es"
    assert manager.set_language("en") == "en"
