"""
Unit tests for the F1 files queue logic (C1 + C2 follow-ups).

Covers the pure status/localization helpers and the enqueue wiring:
- record_file_status: per-file ``(state, reason)`` entries (C2 / LT-4)
- file_reason_text / file_status_label_text: stable reasons localized,
  free-form reasons passed through untouched
- add_files_to_queue (FilesViewMixin harness): unreadable files rejected
  at import time with reason ``unreadable`` (C1 / LT-2)
- lang keys: files queue section keys present, dedicated tab key removed

UI widget rendering is intentionally not unit-tested (headless CI); it is
verified by inspection plus the import smoke test.
"""

import json
import logging
import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pytest

from backend import file_import
from ui.views.files_view import FilesViewMixin

LANG_DIR = Path(__file__).resolve().parents[2] / "lang"


class _FakeLocalization:
    """Duck-typed LocalizationManager mirroring MISSING_TRANSLATION behavior."""

    def __init__(self, strings=None):
        self._strings = dict(strings or {})

    def get_string(self, key, **kwargs):
        text = self._strings.get(key, f"MISSING_TRANSLATION_{key}")
        return text.format(**kwargs)


class _QueueHarness(FilesViewMixin):
    """Headless harness exercising FilesViewMixin queue logic without Tk."""

    def __init__(self, strings=None):
        self.localization_manager = _FakeLocalization(strings)
        self.scheduled = []

    def after(self, ms, fn, *args):
        """Record scheduled UI callbacks instead of touching a Tk loop."""
        self.scheduled.append((fn, args))


def _make_audio(tmp_path, name="clip.ogg"):
    audio = tmp_path / name
    audio.write_bytes(b"x")
    return audio


@pytest.mark.unit
class TestRecordFileStatus:
    """Tests for the pure per-file status recorder (C2 / LT-4)."""

    def test_error_state_keeps_given_reason(self):
        # Arrange
        status_map = {}

        # Act
        entry = file_import.record_file_status(status_map, "a.mp3", "error", "unreadable")

        # Assert
        assert entry == ("error", "unreadable")
        assert status_map["a.mp3"] == ("error", "unreadable")

    def test_error_without_reason_normalizes_to_unknown(self):
        # Act
        entry = file_import.record_file_status({}, "a.mp3", "error", None)

        # Assert
        assert entry == ("error", file_import.REASON_UNKNOWN)

    def test_empty_error_reason_normalizes_to_unknown(self):
        # Act
        entry = file_import.record_file_status({}, "a.mp3", "error", "")

        # Assert
        assert entry == ("error", file_import.REASON_UNKNOWN)

    def test_non_error_states_carry_empty_reason(self):
        # Act / Assert
        assert file_import.record_file_status({}, "a", "pending") == ("pending", "")
        assert file_import.record_file_status({}, "a", "transcribing") == ("transcribing", "")
        assert file_import.record_file_status({}, "a", "done") == ("done", "")

    def test_new_status_overwrites_previous_entry(self):
        # Arrange
        status_map = {"a.mp3": ("pending", "")}

        # Act
        entry = file_import.record_file_status(status_map, "a.mp3", "error", "save_failed")

        # Assert
        assert status_map["a.mp3"] == ("error", "save_failed")
        assert entry == ("error", "save_failed")


@pytest.mark.unit
class TestFileReasonText:
    """Tests for stable-reason localization with free-form passthrough."""

    STRINGS = {
        "files_reason_unreadable": "Archivo ilegible",
        "files_reason_empty_result": "Sin resultado",
        "files_reason_save_failed": "No se pudo guardar",
        "files_reason_unknown": "Motivo desconocido",
    }

    def test_stable_reason_is_localized(self):
        # Act / Assert
        assert file_import.file_reason_text(_FakeLocalization(self.STRINGS), "unreadable") == (
            "Archivo ilegible"
        )

    def test_free_form_reason_is_passed_through_untouched(self):
        # Act / Assert
        assert (
            file_import.file_reason_text(
                _FakeLocalization(self.STRINGS), "ClientError: {bad} format"
            )
            == "ClientError: {bad} format"
        )

    def test_stable_reason_without_translation_key_falls_back_to_raw(self):
        # Act / Assert
        assert file_import.file_reason_text(_FakeLocalization({}), "unreadable") == "unreadable"


@pytest.mark.unit
class TestFileStatusLabelText:
    """Tests for queue label composition (localized state + reason)."""

    STRINGS = {
        "files_status_pending": "Pendiente",
        "files_status_done": "Completado",
        "files_status_error": "Error",
        "files_reason_unreadable": "Archivo ilegible",
    }

    def test_non_error_label_is_localized_state_only(self):
        # Act / Assert
        assert (
            file_import.file_status_label_text(_FakeLocalization(self.STRINGS), ("done", ""))
            == "Completado"
        )

    def test_error_label_appends_localized_reason(self):
        # Act / Assert
        assert (
            file_import.file_status_label_text(
                _FakeLocalization(self.STRINGS), ("error", "unreadable")
            )
            == "Error (Archivo ilegible)"
        )

    def test_error_label_appends_free_form_reason_raw(self):
        # Act / Assert
        assert (
            file_import.file_status_label_text(
                _FakeLocalization(self.STRINGS), ("error", "Timeout: boom")
            )
            == "Error (Timeout: boom)"
        )


@pytest.mark.unit
class TestEnqueueReadableProbe:
    """Tests for the C1 readability probe wired into the enqueue path."""

    STRINGS = {"files_rejected": "Rechazados: {items}"}

    def test_unreadable_file_is_rejected_with_reason(self, tmp_path, monkeypatch):
        # Arrange
        audio = _make_audio(tmp_path, "whatsapp.ogg")

        def boom(path):
            raise RuntimeError("Format not recognised")

        monkeypatch.setattr("soundfile.info", boom)
        app = _QueueHarness(self.STRINGS)

        # Act
        added, rejected = app.add_files_to_queue([str(audio)])

        # Assert
        assert added == []
        assert rejected == [(str(audio), file_import.REASON_UNREADABLE)]
        assert app._files_queue == []

    def test_readable_file_is_enqueued_with_pair_status(self, tmp_path, monkeypatch):
        # Arrange
        audio = _make_audio(tmp_path, "ok.ogg")
        monkeypatch.setattr("soundfile.info", lambda path: SimpleNamespace(frames=1))
        app = _QueueHarness(self.STRINGS)

        # Act
        added, _ = app.add_files_to_queue([str(audio)])

        # Assert
        assert added == [str(audio)]
        assert app._files_status[str(audio)] == ("pending", "")

    def test_unreadable_rejection_logs_warning_with_path(self, tmp_path, monkeypatch, caplog):
        # Arrange
        audio = _make_audio(tmp_path, "whatsapp.ogg")

        def boom(path):
            raise RuntimeError("Format not recognised")

        monkeypatch.setattr("soundfile.info", boom)
        app = _QueueHarness(self.STRINGS)

        # Act
        with caplog.at_level(logging.WARNING, logger="ui.views.files_view"):
            app.add_files_to_queue([str(audio)])

        # Assert
        warnings = [r for r in caplog.records if r.levelno == logging.WARNING]
        assert any(str(audio) in r.getMessage() for r in warnings)


@pytest.mark.unit
class TestMarkFileError:
    """Tests for the single-ERROR-line failure recorder (C2 / LT-4)."""

    def test_marks_error_pair_and_logs_one_error_line(self, tmp_path, caplog):
        # Arrange
        audio = _make_audio(tmp_path, "a.mp3")
        app = _QueueHarness()
        app._ensure_files_queue_state()

        # Act
        with caplog.at_level(logging.ERROR, logger="ui.views.files_view"):
            app._mark_file_error(str(audio), "unreadable")

        # Assert
        assert app._files_status[str(audio)] == ("error", "unreadable")
        errors = [r for r in caplog.records if r.levelno == logging.ERROR]
        assert len(errors) == 1
        assert "unreadable" in errors[0].getMessage()

    def test_missing_reason_becomes_unknown(self, tmp_path, caplog):
        # Arrange
        audio = _make_audio(tmp_path, "a.mp3")
        app = _QueueHarness()
        app._ensure_files_queue_state()

        # Act
        with caplog.at_level(logging.ERROR, logger="ui.views.files_view"):
            app._mark_file_error(str(audio), "")

        # Assert
        assert app._files_status[str(audio)] == ("error", file_import.REASON_UNKNOWN)
        errors = [r for r in caplog.records if r.levelno == logging.ERROR]
        assert len(errors) == 1


@pytest.mark.unit
class TestFilesQueueLangKeys:
    """Language-file contract for the files queue section (C1/C2/C4)."""

    def test_reason_keys_exist_in_both_languages(self):
        # Act
        es = json.loads(LANG_DIR.joinpath("es.json").read_text(encoding="utf-8"))
        en = json.loads(LANG_DIR.joinpath("en.json").read_text(encoding="utf-8"))

        # Assert
        for key in (
            "files_reason_unreadable",
            "files_reason_empty_result",
            "files_reason_save_failed",
            "files_reason_unknown",
        ):
            assert key in es, f"missing {key} in lang/es.json"
            assert key in en, f"missing {key} in lang/en.json"

    def test_dedicated_files_tab_key_is_removed(self):
        # Act
        es = json.loads(LANG_DIR.joinpath("es.json").read_text(encoding="utf-8"))
        en = json.loads(LANG_DIR.joinpath("en.json").read_text(encoding="utf-8"))

        # Assert: C4 removed the dedicated tab; the key must not linger
        assert "tab_files" not in es
        assert "tab_files" not in en

    def test_reason_texts_differ_from_missing_placeholder(self):
        # Act
        es = json.loads(LANG_DIR.joinpath("es.json").read_text(encoding="utf-8"))

        # Assert: every reason key carries real user-facing text
        for key in ("files_reason_unreadable", "files_reason_empty_result"):
            assert es[key] and not es[key].startswith("MISSING")
