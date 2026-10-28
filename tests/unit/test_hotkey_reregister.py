"""Hotkey re-registration via the selector dialog (latent-crash fix).

The dialog path (on_hotkey_selected -> _reregister_hotkey) called two
dead symbols: ``hotkey_display_button`` (never assigned anywhere) and
``_setup_hotkey_system`` (never defined). After ``keyboard.unhook_all()``
the re-registration crashed, leaving the recording hotkey — and the
independently registered pause/capture hotkeys — dead until restart.

These tests pin the delegation to the transcriber's proven
``update_hotkey`` lifecycle, the same API the working inline selector
uses.
"""

import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast
from unittest.mock import MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pytest

from ui.app import App


@pytest.mark.unit
class TestReregisterHotkey:
    """App._reregister_hotkey delegates to transcriber.update_hotkey."""

    def _harness(self):
        return SimpleNamespace(transcriber=MagicMock(), logger=MagicMock())

    def test_delegates_to_transcriber_update_hotkey(self):
        # Arrange
        harness = cast(Any, self._harness())

        # Act
        App._reregister_hotkey(harness, "f10")

        # Assert
        harness.transcriber.update_hotkey.assert_called_once_with("f10")

    def test_transcriber_failure_is_logged_not_raised(self):
        # Arrange
        harness = cast(Any, self._harness())
        harness.transcriber.update_hotkey.side_effect = RuntimeError("boom")

        # Act: must not raise
        App._reregister_hotkey(harness, "f10")

        # Assert
        harness.logger.error.assert_called()

    def test_dead_setup_method_is_gone(self):
        # Arrange: the old path called an undefined symbol; inspect the METHOD
        # body only (a docstring mention of the old line is fine).
        import ast

        src = (
            Path(__file__).resolve().parents[2] / "ui" / "app.py"
        ).read_text(encoding="utf-8")
        tree = ast.parse(src)

        # Act
        method_src = None
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == "_reregister_hotkey":
                method_src = ast.get_source_segment(src, node)
                break

        # Assert
        assert method_src is not None, "_reregister_hotkey not found"
        assert "_setup_hotkey_system" not in method_src
        assert "unhook_all" not in method_src
