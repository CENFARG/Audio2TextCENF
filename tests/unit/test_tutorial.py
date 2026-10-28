"""Tutorial steps contract (S8/S10).

S8: the tutorial must explain the WhatsApp/files queue section.
S10: the prompt enhancer (Prompter) only makes sense when the Supervisor
workbench is enabled (S6 ships it hidden), so its step is conditional.
"""

import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pytest

from ui.tutorial import TutorialManager

LANG_DIR = Path(__file__).resolve().parents[2] / "lang"


class _FakeLoc:
    """Duck-typed LocalizationManager returning the raw key."""

    def get_string(self, key, **kwargs):
        return str(key)


def _make_app(supervisor_enabled: bool) -> SimpleNamespace:
    return SimpleNamespace(
        localization_manager=_FakeLoc(),
        config_manager=SimpleNamespace(
            get=lambda key, default=None: supervisor_enabled if key == "supervisor_tab_enabled" else default
        ),
    )


@pytest.mark.unit
class TestTutorialSteps:
    def test_whatsapp_section_step_exists(self):
        # Act
        titles = [s["title"] for s in TutorialManager(_make_app(False)).steps]

        # Assert: S8 — the files/WhatsApp queue is explained
        assert "Audios de WhatsApp" in titles

    def test_whatsapp_step_targets_the_files_section(self):
        # Act
        steps = TutorialManager(_make_app(False)).steps
        step = next(s for s in steps if s["title"] == "Audios de WhatsApp")

        # Assert: tooltip lands on the collapsible section header
        assert step.get("target") == "files_toggle_button"

    def test_prompter_step_hidden_without_supervisor(self):
        # Act
        titles = [s["title"] for s in TutorialManager(_make_app(False)).steps]

        # Assert: S6+S10 — no confusion about a hidden workbench
        assert "Mejorador de prompt" not in titles

    def test_prompter_step_present_with_supervisor_enabled(self):
        # Act
        titles = [s["title"] for s in TutorialManager(_make_app(True)).steps]

        # Assert: dev builds still teach the Prompter (S10)
        assert "Mejorador de prompt" in titles

    def test_step_structure_preserved(self):
        # Arrange: every step keeps the documented shape
        steps = TutorialManager(_make_app(True)).steps

        # Act / Assert
        for step in steps:
            assert "title" in step and "message" in step
            assert "tab" in step

    def test_tutorial_lang_keys_still_localized(self):
        # Arrange: the tutorial tabs route through i18n keys (tab_main etc.)
        es = dict(__import__("json").loads(LANG_DIR.joinpath("es.json").read_text(encoding="utf-8")))

        # Act / Assert: keys used by the static steps keep existing
        for key in ("tab_main", "tab_settings", "tab_history"):
            assert key in es, f"missing {key} in lang/es.json"
