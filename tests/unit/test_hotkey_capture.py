"""
Unit tests for the F3 global hotkey capture into the supervisor workbench.

Covers the pure decision logic and the handler contract (no UI imports):
- ``decide_capture_action``: strip-compare against the last entry response;
  empty/whitespace clipboard is ignored.
- ``build_capture_entry``: deterministic payload for a fresh capture entry.
- ``HotkeyCaptureHandler.on_trigger``: reads the clipboard via the injected
  reader and either creates a new entry (response = clipboard text) or
  replaces the LAST entry's response; returns a localized-message key.
"""

import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pytest

from backend.hotkey_capture import (
    HotkeyCaptureHandler,
    MESSAGE_KEY_NEW,
    MESSAGE_KEY_REPLACED,
    build_capture_entry,
    decide_capture_action,
)
from backend.supervisor_store import SupervisorStore


# ── decide_capture_action (pure) ────────────────────────────────────────
@pytest.mark.unit
class TestDecideCaptureAction:
    @pytest.mark.parametrize("empty_text", ["", "   ", "\n\t ", None])
    def test_empty_clipboard_is_ignored(self, empty_text):
        assert decide_capture_action(empty_text, None) == "ignore"
        assert decide_capture_action(empty_text, "texto previo") == "ignore"

    def test_no_previous_entry_is_new(self):
        assert decide_capture_action("texto nuevo", None) == "new"
        assert decide_capture_action("texto nuevo", "") == "new"

    def test_same_text_replaces_last(self):
        assert decide_capture_action("hola mundo", "hola mundo") == "replace_last"

    def test_strip_compare_replaces_last(self):
        assert decide_capture_action("  hola mundo\n", "hola mundo  ") == "replace_last"

    def test_different_text_is_new(self):
        assert decide_capture_action("texto nuevo", "texto viejo") == "new"

    def test_compare_is_case_sensitive_strip_only(self):
        # Contract: strip-compare only — no case folding, no punctuation stripping.
        assert decide_capture_action("Hola", "hola") == "new"


# ── build_capture_entry (pure) ──────────────────────────────────────────
@pytest.mark.unit
class TestBuildCaptureEntry:
    def test_payload_shape(self):
        payload = build_capture_entry("texto capturado", 7)
        assert payload == {"number": 7, "quote": "", "response": "texto capturado"}

    def test_payload_is_a_fresh_dict_each_call(self):
        first = build_capture_entry("a", 1)
        second = build_capture_entry("b", 2)
        first["response"] = "mutado"
        assert second == {"number": 2, "quote": "", "response": "b"}


# ── HotkeyCaptureHandler (real SupervisorStore, injected clipboard) ─────
@pytest.mark.unit
class TestHotkeyCaptureHandler:
    @pytest.fixture
    def store(self, tmp_path):
        return SupervisorStore(tmp_path / "entries.json")

    def _handler(self, store, clipboard_value):
        return HotkeyCaptureHandler(store, lambda: clipboard_value)

    def test_new_capture_creates_entry_with_clipboard_response(self, store):
        handler = self._handler(store, "respuesta de la IA")
        result = handler.on_trigger()

        assert result is not None
        assert result.message_key == MESSAGE_KEY_NEW
        entries = store.all()
        assert len(entries) == 1
        assert entries[0].response == "respuesta de la IA"
        assert result.entry.number == entries[0].number

    def test_same_clipboard_replaces_last_entry_without_creating(self, store):
        store.create_entry(response="versión vieja")
        handler = self._handler(store, "versión vieja")

        result = handler.on_trigger()

        assert result is not None
        assert result.message_key == MESSAGE_KEY_REPLACED
        entries = store.all()
        assert len(entries) == 1  # no duplicate entry
        assert entries[0].response == "versión vieja"

    def test_replace_updates_only_the_last_entry_response(self, store):
        store.create_entry(response="primera")
        last = store.create_entry(response="segunda")
        handler = self._handler(store, "segunda ")

        result = handler.on_trigger()

        assert result is not None
        entries = store.all()
        assert len(entries) == 2
        assert entries[0].response == "primera"  # untouched
        assert entries[-1].number == last.number
        assert entries[-1].response == "segunda"
        assert result.entry.number == last.number

    def test_empty_clipboard_is_ignored_and_store_untouched(self, store):
        handler = self._handler(store, "   ")
        assert handler.on_trigger() is None
        assert store.all() == []

    def test_clipboard_reader_error_is_logged_and_ignored(self, store, caplog):
        def broken_reader():
            raise RuntimeError("clipboard unavailable")

        handler = HotkeyCaptureHandler(store, broken_reader)
        with caplog.at_level(logging.WARNING, logger="backend.hotkey_capture"):
            assert handler.on_trigger() is None
        assert store.all() == []
        assert "clipboard" in caplog.text.lower()
