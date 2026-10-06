"""
Unit tests for the F2 Supervisor view PURE glue (headless, no Tk).

Covers only the pure pieces extracted from SupervisorViewMixin so the mixin
stays thin and Tk widgets are verified by inspection + import smoke:
- DebounceTimer: autosave debounce logic (schedule/reschedule/cancel)
- Tk cursor-index glue: parse "line.col" -> char offset, insert-at-cursor
- entry selection state: keep selection, fall back to first, None when empty
- block-id recording glue: append without duplicates
- assembled-copy formatting glue: build_copy_payload delegates to the store
  assembler (order + blank-line separation)
- lang parity: every supervisor_* key present in BOTH lang/es.json and
  lang/en.json (i18n requirement)
"""

import json
import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pytest

from ui.views import supervisor_view as sv
from ui.views.supervisor_view import (
    AUTOSAVE_DEBOUNCE_MS,
    DebounceTimer,
    append_block_id,
    build_copy_payload,
    compute_inserted_text,
    compute_multi_insert,
    format_entry_label,
    parse_tk_index,
    resolve_selection,
    select_blocks,
    tk_index_to_char_index,
)

LANG_DIR = Path(__file__).resolve().parents[2] / "lang"

SUPERVISOR_LANG_KEYS = [
    "tab_supervisor",
    "supervisor_title",
    "supervisor_new_entry",
    "supervisor_insert_block",
    "supervisor_copy_entry",
    "supervisor_copy_all",
    "supervisor_status_draft",
    "supervisor_status_sent",
    "supervisor_delete_confirm",
    "supervisor_record",
    "supervisor_record_stop",
    "supervisor_recording_blocked",
    "supervisor_quote_placeholder",
    "supervisor_response_placeholder",
    "supervisor_copied",
    "supervisor_deleted",
    "supervisor_no_blocks",
    "supervisor_select_entry_first",
    "supervisor_copy_empty",
    "supervisor_recording_error",
    "supervisor_busy",
    "supervisor_transcribing",
    "supervisor_transcribed",
    "supervisor_transcription_failed",
    "supervisor_mark_sent",
    "supervisor_reopen",
    "supervisor_blocks_button",
    "supervisor_blocks_title",
    "supervisor_insert_selected",
    "supervisor_close",
    "supervisor_session_label",
    "supervisor_session_filter",
]


class _FakeAfter:
    """Fake Tk ``after``/``after_cancel`` pair recording scheduled calls."""

    def __init__(self) -> None:
        self.scheduled: list[tuple[int, object]] = []
        self.cancelled: list[object] = []
        self._next_id = 0

    def after(self, ms, fn, *args) -> int:
        self._next_id += 1
        self.scheduled.append((ms, fn))
        return self._next_id

    def after_cancel(self, token) -> None:
        self.cancelled.append(token)


@pytest.mark.unit
class TestDebounceTimer:
    """Autosave debounce: trailing-edge, one pending flush at a time."""

    def test_default_delay_is_at_least_500ms(self):
        # Assert: spec requires >= 500 ms debounce
        assert AUTOSAVE_DEBOUNCE_MS >= 500
        assert DebounceTimer().delay_ms == AUTOSAVE_DEBOUNCE_MS

    def test_schedule_uses_after_with_delay_and_flush(self):
        # Arrange
        fake = _FakeAfter()
        timer = DebounceTimer()

        # Act
        token = timer.schedule(fake.after, fake.after_cancel, lambda: None)

        # Assert
        assert token is not None
        assert len(fake.scheduled) == 1
        assert fake.scheduled[0][0] == AUTOSAVE_DEBOUNCE_MS

    def test_reschedule_cancels_previous_pending_flush(self):
        # Arrange
        fake = _FakeAfter()
        timer = DebounceTimer()
        first_token = timer.schedule(fake.after, fake.after_cancel, lambda: None)

        # Act
        timer.schedule(fake.after, fake.after_cancel, lambda: None)

        # Assert: previous token cancelled, exactly one pending flush
        assert fake.cancelled == [first_token]
        assert len(fake.scheduled) == 2

    def test_cancel_without_pending_is_noop(self):
        # Arrange
        fake = _FakeAfter()
        timer = DebounceTimer()

        # Act / Assert
        assert timer.cancel(fake.after_cancel) is False
        assert fake.cancelled == []

    def test_cancel_invokes_after_cancel_and_clears_pending(self):
        # Arrange
        fake = _FakeAfter()
        timer = DebounceTimer()
        token = timer.schedule(fake.after, fake.after_cancel, lambda: None)

        # Act
        assert timer.cancel(fake.after_cancel) is True

        # Assert
        assert fake.cancelled == [token]
        assert timer.pending is False


@pytest.mark.unit
class TestCursorGlue:
    """Tk "line.col" -> char offset and insert-at-cursor composition."""

    CONTENT = "hola\nmundo\nfin"

    def test_parse_tk_index(self):
        # Act / Assert
        assert parse_tk_index("2.3") == (2, 3)
        assert parse_tk_index("garbage") == (1, 0)
        assert parse_tk_index("1.0") == (1, 0)

    def test_char_index_line_col(self):
        # Act / Assert: line 1 col n -> n; line 2 starts after "hola\n" (5)
        assert tk_index_to_char_index(self.CONTENT, 1, 0) == 0
        assert tk_index_to_char_index(self.CONTENT, 1, 2) == 2
        assert tk_index_to_char_index(self.CONTENT, 2, 0) == 5
        assert tk_index_to_char_index(self.CONTENT, 2, 3) == 8

    def test_char_index_clamps_out_of_range(self):
        # Act / Assert: line beyond end -> end of content; col beyond line -> line end
        assert tk_index_to_char_index(self.CONTENT, 99, 0) == len(self.CONTENT)
        assert tk_index_to_char_index(self.CONTENT, 1, 999) == 4

    def test_compute_inserted_text_positions(self):
        # Act / Assert: middle, start, end, None (append)
        assert compute_inserted_text("abcd", "X", 2) == "abXcd"
        assert compute_inserted_text("abcd", "X", 0) == "Xabcd"
        assert compute_inserted_text("abcd", "X", 4) == "abcdX"
        assert compute_inserted_text("abcd", "X", None) == "abcdX"
        assert compute_inserted_text("", "body", None) == "body"


@pytest.mark.unit
class TestSelectionState:
    """Entry selection: sticky, falls back to first, None when empty."""

    def test_keeps_current_when_still_present(self):
        # Act / Assert
        assert resolve_selection([1, 2, 3], 2) == 2

    def test_falls_back_to_first_when_current_missing(self):
        # Act / Assert: e.g. after deleting the selected entry
        assert resolve_selection([1, 3, 4], 2) == 1

    def test_none_when_no_entries(self):
        # Act / Assert
        assert resolve_selection([], 7) is None


@pytest.mark.unit
class TestRowGlue:
    """Block-id recording and row-label formatting."""

    def test_append_block_id_no_duplicates(self):
        # Act / Assert
        assert append_block_id(["a", "b"], "c") == ["a", "b", "c"]
        assert append_block_id(["a", "b"], "a") == ["a", "b"]
        assert append_block_id([], "") == []

    def test_format_entry_label(self):
        # Act / Assert
        assert format_entry_label(3, "borrador") == "#3 · borrador"


@pytest.mark.unit
class TestBlockMultiSelect:
    """REQ-3: checkbox state {block_id: bool} -> ordered selected blocks."""

    @staticmethod
    def _blocks():
        # Loaded order is sorted by name (load_context_blocks contract).
        return [
            SimpleNamespace(id="alpha", name="Alpha", description="d-a", body="A"),
            SimpleNamespace(id="mike", name="Mike", description="d-m", body="M"),
            SimpleNamespace(id="zulu", name="Zulu", description="d-z", body="Z"),
        ]

    def test_returns_checked_blocks_in_list_order(self):
        state = {"zulu": True, "alpha": True}

        # Act
        selected = select_blocks(state, self._blocks())

        # Assert: list order (Alpha, Zulu), NOT dict/check order.
        assert [b.id for b in selected] == ["alpha", "zulu"]

    def test_unchecked_and_missing_keys_are_excluded(self):
        state = {"alpha": False, "mike": True}

        # Act
        selected = select_blocks(state, self._blocks())

        # Assert
        assert [b.id for b in selected] == ["mike"]

    def test_unknown_ids_in_state_are_ignored(self):
        state = {"ghost": True, "mike": True}

        # Act
        selected = select_blocks(state, self._blocks())

        # Assert
        assert [b.id for b in selected] == ["mike"]

    def test_empty_state_selects_nothing(self):
        # Act / Assert
        assert select_blocks({}, self._blocks()) == []

    def test_no_blocks_selects_nothing(self):
        # Act / Assert
        assert select_blocks({"alpha": True}, []) == []


@pytest.mark.unit
class TestComputeMultiInsert:
    """REQ-3: insert several block bodies at the cursor, in list order."""

    def test_inserts_in_order_at_cursor(self):
        # Act
        result = compute_multi_insert("AB--GH", ["CD", "EF"], 3)

        # Assert: CD lands at cursor 3 (between the dashes), EF follows CD;
        # order preserved, cursor advanced by each body length.
        assert result == "AB-CDEF-GH"

    def test_inserts_in_order_at_start(self):
        # Act / Assert
        assert compute_multi_insert("world", ["hello ", "big "], 0) == "hello big world"

    def test_none_cursor_appends_in_order(self):
        # Act / Assert
        assert compute_multi_insert("end", [" A", " B"], None) == "end A B"

    def test_multiline_bodies_keep_cursor_math(self):
        # Act
        result = compute_multi_insert("x|y", ["one\ntwo", "!"], 2)

        # Assert: "one\ntwo" (7 chars) lands before "y", cursor advances by
        # each body length (newline counts as 1), then "!" lands after it.
        assert result == "x|one\ntwo!y"

    def test_empty_selection_leaves_content_unchanged(self):
        # Act / Assert
        assert compute_multi_insert("same", [], 2) == "same"


@pytest.mark.unit
class TestCopyPayloadGlue:
    """Assembled-copy glue: numeric order, blank-line separated."""

    def test_build_copy_payload_uses_store_assembler(self):
        # Arrange
        entries = [
            SimpleNamespace(number=1, quote="q1", response="r1"),
            SimpleNamespace(number=2, quote="", response="r2"),
        ]

        # Act
        payload = build_copy_payload(entries)

        # Assert
        assert payload == '1. "q1"\n: r1\n\n2. r2'

    def test_build_copy_payload_empty(self):
        # Act / Assert
        assert build_copy_payload([]) == ""


@pytest.mark.unit
class TestLangParity:
    """Every supervisor key exists in BOTH lang files (i18n requirement)."""

    @pytest.mark.parametrize("lang", ["es", "en"])
    def test_supervisor_keys_present(self, lang):
        # Arrange
        translations = json.loads((LANG_DIR / f"{lang}.json").read_text(encoding="utf-8"))

        # Act
        missing = [key for key in SUPERVISOR_LANG_KEYS if key not in translations]

        # Assert
        assert missing == []

    @pytest.mark.parametrize("key", ["supervisor_copy_entry", "supervisor_delete_confirm"])
    def test_placeholder_keys_are_formattable(self, key):
        # Arrange: keys with {number} must survive .format(number=...)
        for lang in ("es", "en"):
            translations = json.loads((LANG_DIR / f"{lang}.json").read_text(encoding="utf-8"))

            # Act / Assert
            assert "{number}" in translations[key]
            assert translations[key].format(number=7)


@pytest.mark.unit
class TestSessionGlue:
    """REQ-2: session-filter selection + row-label format with session."""

    @staticmethod
    def _entries():
        return [
            SimpleNamespace(number=1, session="gemini"),
            SimpleNamespace(number=2, session="general"),
            SimpleNamespace(number=3, session="gemini"),
        ]

    def test_filter_on_keeps_only_current_session_in_order(self):
        # Act
        visible = sv.select_visible_entries(self._entries(), "gemini", True)

        # Assert
        assert [e.number for e in visible] == [1, 3]

    def test_filter_off_shows_all_sessions(self):
        # Act
        visible = sv.select_visible_entries(self._entries(), "gemini", False)

        # Assert
        assert [e.number for e in visible] == [1, 2, 3]

    def test_filter_on_without_matches_is_empty(self):
        # Act / Assert
        assert sv.select_visible_entries(self._entries(), "claude", True) == []

    def test_row_label_includes_session(self):
        # Act / Assert: REQ-2 row format "#1 · borrador · agente-x"
        assert sv.format_entry_label(1, "borrador", "agente-x") == "#1 · borrador · agente-x"

    def test_row_label_without_session_stays_two_part(self):
        # Act / Assert: previous two-arg behavior preserved
        assert format_entry_label(3, "borrador") == "#3 · borrador"
