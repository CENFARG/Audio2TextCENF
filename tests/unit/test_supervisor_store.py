"""
Unit tests for the F2 Supervisor entry store (pure module).

Covers the JSON-backed workbench contract (openspec audio2text-f2-supervisor):
- SupervisorEntry model: sequential numbers, ISO-8601 timestamps
- CRUD: create / update / delete / set_status, all persisted immediately
- Persist-reload: a fresh store instance sees every acknowledged change
- Atomic write: temp file + os.replace, no ``.tmp`` leftovers
- Corrupt file: backup as ``<name>.corrupt-<timestamp>`` + empty start
- Number stability: deleted numbers are NEVER reassigned
- State machine: draft -> sent -> draft legal; unknown/same transitions
  are no-ops with a logged warning
- REQ-2 sessions: DEFAULT_SESSION contract, create/set_session persistence,
  entries_by_session filter, assemble_session and the no-``session`` JSON
  migration to "general"
"""

import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pytest

from backend import supervisor_store
from backend.supervisor_store import (
    STATUS_DRAFT,
    STATUS_SENT,
    SupervisorEntry,
    SupervisorStore,
)


class _FakeClock:
    """Monotonic fake clock so every timestamp read is strictly newer."""

    def __init__(self) -> None:
        self.ticks = 0

    def __call__(self) -> str:
        self.ticks += 1
        return datetime(2026, 9, 25, 12, 0, self.ticks, tzinfo=timezone.utc).isoformat()


@pytest.mark.unit
class TestSupervisorEntryModel:
    """Entry dataclass shape: required fields and defaults."""

    def test_entry_defaults_to_draft_with_block_list(self):
        # Act
        entry = SupervisorEntry(
            number=1,
            quote="",
            response="r",
            blocks=[],
            status=STATUS_DRAFT,
            created_at="2026-09-25T12:00:00+00:00",
            updated_at="2026-09-25T12:00:00+00:00",
        )

        # Assert
        assert entry.number == 1
        assert entry.status == "draft"
        assert entry.blocks == []
        assert entry.quote == ""
        assert entry.response == "r"

    def test_status_constants_are_stable_strings(self):
        # Assert (state machine vocabulary is contract)
        assert STATUS_DRAFT == "draft"
        assert STATUS_SENT == "sent"


@pytest.mark.unit
class TestStoreCrud:
    """Create / update / delete / status against a temp JSON file."""

    def test_create_assigns_sequential_numbers_and_draft_status(self, tmp_path):
        # Arrange
        store = SupervisorStore(tmp_path / "entries.json", now_fn=_FakeClock())

        # Act
        e1 = store.create_entry()
        e2 = store.create_entry(quote="q", response="r")

        # Assert
        assert (e1.number, e2.number) == (1, 2)
        assert e1.status == STATUS_DRAFT
        assert e2.quote == "q"
        assert e2.response == "r"
        assert e2.blocks == []

    def test_create_sets_iso_timestamps(self, tmp_path):
        # Arrange
        store = SupervisorStore(tmp_path / "entries.json")

        # Act
        entry = store.create_entry()

        # Assert
        assert datetime.fromisoformat(entry.created_at) is not None
        assert datetime.fromisoformat(entry.updated_at) is not None

    def test_update_entry_changes_fields_and_refreshes_updated_at(self, tmp_path):
        # Arrange
        clock = _FakeClock()
        store = SupervisorStore(tmp_path / "entries.json", now_fn=clock)
        entry = store.create_entry()
        created_at = entry.created_at
        updated_at = entry.updated_at

        # Act
        updated = store.update_entry(entry.number, quote="cita", response="respuesta")

        # Assert
        assert updated is not None
        assert updated.quote == "cita"
        assert updated.response == "respuesta"
        assert updated.created_at == created_at
        assert updated.updated_at != updated_at

    def test_update_unknown_number_returns_none(self, tmp_path):
        # Arrange
        store = SupervisorStore(tmp_path / "entries.json", now_fn=_FakeClock())

        # Act / Assert
        assert store.update_entry(99, response="x") is None

    def test_update_does_not_allow_renumbering(self, tmp_path):
        # Arrange
        store = SupervisorStore(tmp_path / "entries.json", now_fn=_FakeClock())
        entry = store.create_entry()

        # Act: ``number`` is not a mutable field; keyword collision avoided via a var
        fields = {"number": 42}
        updated = store.update_entry(entry.number, **fields)

        # Assert
        assert updated is not None
        assert updated.number == entry.number == 1

    def test_delete_removes_entry_and_persists(self, tmp_path):
        # Arrange
        store = SupervisorStore(tmp_path / "entries.json", now_fn=_FakeClock())
        store.create_entry()
        e2 = store.create_entry()

        # Act
        assert store.delete_entry(e2.number) is True

        # Assert
        assert [e.number for e in store.all()] == [1]
        assert store.get(e2.number) is None

    def test_delete_unknown_number_returns_false(self, tmp_path):
        # Arrange
        store = SupervisorStore(tmp_path / "entries.json", now_fn=_FakeClock())

        # Act / Assert
        assert store.delete_entry(99) is False

    def test_set_status_legal_transitions(self, tmp_path):
        # Arrange
        store = SupervisorStore(tmp_path / "entries.json", now_fn=_FakeClock())
        entry = store.create_entry()

        # Act / Assert: draft -> sent
        sent = store.set_status(entry.number, STATUS_SENT)
        assert sent is not None
        assert sent.status == STATUS_SENT
        # Act / Assert: sent -> draft (reopen allowed)
        reopened = store.set_status(entry.number, STATUS_DRAFT)
        assert reopened is not None
        assert reopened.status == STATUS_DRAFT

    def test_set_status_unknown_value_is_noop_with_warning(self, tmp_path, caplog):
        # Arrange
        store = SupervisorStore(tmp_path / "entries.json", now_fn=_FakeClock())
        entry = store.create_entry()

        # Act
        with caplog.at_level(logging.WARNING, logger="backend.supervisor_store"):
            result = store.set_status(entry.number, "weird")

        # Assert: illegal transition is a no-op with a logged warning
        assert result is None
        assert [e.status for e in store.all()] == [STATUS_DRAFT]
        assert any(
            "illegal" in r.message.lower() or "status" in r.message.lower() for r in caplog.records
        )

    def test_set_status_same_status_is_noop_with_warning(self, tmp_path, caplog):
        # Arrange
        clock = _FakeClock()
        store = SupervisorStore(tmp_path / "entries.json", now_fn=clock)
        entry = store.create_entry()
        updated_at = entry.updated_at

        # Act
        with caplog.at_level(logging.WARNING, logger="backend.supervisor_store"):
            store.set_status(entry.number, STATUS_DRAFT)

        # Assert: timestamp untouched, warning logged
        current = store.get(entry.number)
        assert current is not None
        assert current.updated_at == updated_at
        assert len(caplog.records) == 1


@pytest.mark.unit
class TestStorePersistence:
    """Every mutation is acknowledged on disk (autosave, atomic)."""

    def test_reload_sees_all_changes(self, tmp_path):
        # Arrange
        path = tmp_path / "entries.json"
        store = SupervisorStore(path, now_fn=_FakeClock())
        e1 = store.create_entry(quote="q1", response="r1")
        e2 = store.create_entry(quote="q2", response="r2")
        store.update_entry(e1.number, response="r1-edited")
        store.set_status(e2.number, STATUS_SENT)

        # Act
        reloaded = SupervisorStore(path, now_fn=_FakeClock())

        # Assert
        entries = reloaded.all()
        assert [e.number for e in entries] == [1, 2]
        assert entries[0].response == "r1-edited"
        assert entries[1].status == STATUS_SENT
        assert entries[1].quote == "q2"

    def test_all_returns_entries_sorted_by_number(self, tmp_path):
        # Arrange
        store = SupervisorStore(tmp_path / "entries.json", now_fn=_FakeClock())
        for _ in range(3):
            store.create_entry()

        # Act / Assert
        assert [e.number for e in store.all()] == [1, 2, 3]

    def test_save_is_atomic_no_tmp_leftover_and_valid_json(self, tmp_path):
        # Arrange
        path = tmp_path / "entries.json"
        store = SupervisorStore(path, now_fn=_FakeClock())

        # Act
        store.create_entry(response="hola")

        # Assert: temp+replace leaves no partial artifact and the file parses
        assert not (tmp_path / "entries.json.tmp").exists()
        payload = json.loads(path.read_text(encoding="utf-8"))
        assert payload["entries"][0]["response"] == "hola"
        assert payload["entries"][0]["number"] == 1

    def test_empty_store_creates_no_file_until_first_mutation(self, tmp_path):
        # Arrange / Act
        store = SupervisorStore(tmp_path / "entries.json", now_fn=_FakeClock())

        # Assert: load-only construction must not write
        assert not (tmp_path / "entries.json").exists()
        assert store.all() == []


@pytest.mark.unit
class TestCorruptFileHandling:
    """Corrupt store file: backup + empty start + logged error (never crash)."""

    def test_corrupt_file_backed_up_and_store_starts_empty(self, tmp_path, caplog):
        # Arrange
        path = tmp_path / "entries.json"
        path.write_text("{ this is not json", encoding="utf-8")

        # Act
        with caplog.at_level(logging.ERROR, logger="backend.supervisor_store"):
            store = SupervisorStore(path, now_fn=_FakeClock())

        # Assert: empty start, backup created, original preserved, error logged
        assert store.all() == []
        backups = list(tmp_path.glob("entries.json.corrupt-*"))
        assert len(backups) == 1
        assert backups[0].read_text(encoding="utf-8") == "{ this is not json"
        assert path.exists()
        assert any(r.levelno == logging.ERROR for r in caplog.records)

    def test_corrupt_file_can_save_fresh_entries_after_backup(self, tmp_path):
        # Arrange
        path = tmp_path / "entries.json"
        path.write_text("garbage", encoding="utf-8")
        store = SupervisorStore(path, now_fn=_FakeClock())

        # Act
        entry = store.create_entry(response="nuevo")

        # Assert: store usable after recovery, backup untouched
        restored = store.get(entry.number)
        assert restored is not None
        assert restored.response == "nuevo"
        assert len(list(tmp_path.glob("entries.json.corrupt-*"))) == 1

    def test_non_dict_root_is_corrupt(self, tmp_path):
        # Arrange
        path = tmp_path / "entries.json"
        path.write_text("[1, 2, 3]", encoding="utf-8")

        # Act
        store = SupervisorStore(path, now_fn=_FakeClock())

        # Assert
        assert store.all() == []
        assert len(list(tmp_path.glob("entries.json.corrupt-*"))) == 1

    def test_malformed_entries_are_skipped_not_fatal(self, tmp_path):
        # Arrange: one good entry, one malformed (missing number)
        path = tmp_path / "entries.json"
        payload = {
            "version": 1,
            "entries": [
                {
                    "number": 1,
                    "quote": "",
                    "response": "ok",
                    "blocks": [],
                    "status": "draft",
                    "created_at": "2026-09-25T12:00:01+00:00",
                    "updated_at": "2026-09-25T12:00:01+00:00",
                },
                {"quote": "no number here"},
                "not-even-a-dict",
            ],
        }
        path.write_text(json.dumps(payload), encoding="utf-8")

        # Act
        store = SupervisorStore(path, now_fn=_FakeClock())

        # Assert
        assert [e.number for e in store.all()] == [1]


@pytest.mark.unit
class TestNumberStability:
    """Numbers are historical: deleting never renumbers remaining entries."""

    def test_numbers_not_reassigned_after_delete(self, tmp_path):
        # Arrange
        store = SupervisorStore(tmp_path / "entries.json", now_fn=_FakeClock())
        store.create_entry()
        store.create_entry()
        store.create_entry()
        store.delete_entry(2)

        # Act
        e4 = store.create_entry()

        # Assert: next number is max(existing)+1, gaps preserved
        assert e4.number == 4
        assert [e.number for e in store.all()] == [1, 3, 4]

    def test_deleted_max_number_is_never_reused(self, tmp_path):
        # Arrange: C-2 — deleting the highest entry must not free its number
        store = SupervisorStore(tmp_path / "entries.json", now_fn=_FakeClock())
        store.create_entry()
        last = store.create_entry()
        store.delete_entry(last.number)

        # Act
        entry = store.create_entry()

        # Assert: the counter never walks back, even past the deleted max
        assert entry.number == 3
        assert [e.number for e in store.all()] == [1, 3]

    def test_persisted_counter_survives_reload_after_deleting_max(self, tmp_path):
        # Arrange: C-2 — the counter persists, so a reload cannot reuse #2
        path = tmp_path / "entries.json"
        store = SupervisorStore(path, now_fn=_FakeClock())
        store.create_entry()
        last = store.create_entry()
        store.delete_entry(last.number)

        # Act
        reloaded = SupervisorStore(path, now_fn=_FakeClock())
        entry = reloaded.create_entry()

        # Assert
        assert entry.number == 3

    def test_saved_payload_carries_next_number(self, tmp_path):
        # Arrange
        path = tmp_path / "entries.json"
        store = SupervisorStore(path, now_fn=_FakeClock())

        # Act
        store.create_entry()

        # Assert
        payload = json.loads(path.read_text(encoding="utf-8"))
        assert payload["next_number"] == 2

    def test_migration_absent_counter_initializes_max_plus_one(self, tmp_path):
        # Arrange: legacy JSON without ``next_number`` (pre C-2 schema)
        path = tmp_path / "entries.json"
        path.write_text(
            json.dumps({"version": 1, "entries": [{"number": 1}, {"number": 5}]}),
            encoding="utf-8",
        )

        # Act
        store = SupervisorStore(path, now_fn=_FakeClock())
        entry = store.create_entry()

        # Assert: migrated to max(existing)+1 = 6, then persisted as 7
        assert entry.number == 6
        payload = json.loads(path.read_text(encoding="utf-8"))
        assert payload["next_number"] == 7

    def test_number_sequence_survives_reload(self, tmp_path):
        # Arrange
        path = tmp_path / "entries.json"
        store = SupervisorStore(path, now_fn=_FakeClock())
        store.create_entry()
        store.create_entry()
        store.delete_entry(2)
        reloaded = SupervisorStore(path, now_fn=_FakeClock())

        # Act: C-2 — the persisted counter keeps the deleted number consumed
        entry = reloaded.create_entry()

        # Assert: sequence does NOT reset to 1 and does NOT reuse deleted #2
        assert entry.number == 3


@pytest.mark.unit
class TestModuleHelpers:
    """Dict <-> entry conversion used for JSON persistence."""

    def test_roundtrip_entry_through_dict(self):
        # Arrange
        entry = SupervisorEntry(
            number=7,
            quote='dijo "algo"',
            response="r",
            blocks=["b1", "b2"],
            status=STATUS_SENT,
            created_at="2026-09-25T12:00:01+00:00",
            updated_at="2026-09-25T12:00:02+00:00",
        )

        # Act
        restored = supervisor_store._entry_from_dict(supervisor_store._entry_to_dict(entry))

        # Assert
        assert restored == entry

    def test_from_dict_defaults_missing_optional_fields(self):
        # Act
        entry = supervisor_store._entry_from_dict({"number": 1})

        # Assert
        assert entry.quote == ""
        assert entry.response == ""
        assert entry.blocks == []
        assert entry.status == STATUS_DRAFT


@pytest.mark.unit
class TestSessions:
    """REQ-2: per-entry session — default, set/persist, filter and assembly."""

    def test_default_session_constant_is_general(self):
        # Assert: the session vocabulary is contract (UI + migration rely on it)
        assert supervisor_store.DEFAULT_SESSION == "general"

    def test_entry_defaults_session_to_general(self):
        # Act
        entry = SupervisorEntry(number=1)

        # Assert
        assert entry.session == "general"

    def test_create_entry_captures_given_session(self, tmp_path):
        # Arrange
        store = SupervisorStore(tmp_path / "entries.json", now_fn=_FakeClock())

        # Act
        entry = store.create_entry(session="agente-x")

        # Assert
        assert entry.session == "agente-x"

    def test_create_entry_blank_session_falls_back_to_general(self, tmp_path):
        # Arrange
        store = SupervisorStore(tmp_path / "entries.json", now_fn=_FakeClock())

        # Act / Assert: a session is never persisted as an empty string
        assert store.create_entry(session="   ").session == "general"

    def test_set_session_changes_and_persists_across_reload(self, tmp_path):
        # Arrange
        path = tmp_path / "entries.json"
        store = SupervisorStore(path, now_fn=_FakeClock())
        entry = store.create_entry()
        updated_at = entry.updated_at

        # Act
        updated = store.set_session(entry.number, "gemini")

        # Assert: mutation bumps updated_at and survives a fresh load
        assert updated is not None
        assert updated.session == "gemini"
        assert updated.updated_at != updated_at
        reloaded = SupervisorStore(path, now_fn=_FakeClock())
        assert reloaded.get(entry.number).session == "gemini"

    def test_set_session_unknown_number_returns_none(self, tmp_path):
        # Arrange
        store = SupervisorStore(tmp_path / "entries.json", now_fn=_FakeClock())

        # Act / Assert
        assert store.set_session(99, "gemini") is None

    def test_entries_by_session_filters_in_number_order(self, tmp_path):
        # Arrange
        store = SupervisorStore(tmp_path / "entries.json", now_fn=_FakeClock())
        e1 = store.create_entry(session="gemini")
        e2 = store.create_entry()
        e3 = store.create_entry(session="gemini")
        store.create_entry(session="claude")

        # Act / Assert: numeric order inside each session, unknown session empty
        assert [e.number for e in store.entries_by_session("gemini")] == [e1.number, e3.number]
        assert [e.number for e in store.entries_by_session("general")] == [e2.number]
        assert store.entries_by_session("sin-entradas") == []

    def test_assemble_session_joins_only_that_session_in_number_order(self, tmp_path):
        # Arrange
        store = SupervisorStore(tmp_path / "entries.json", now_fn=_FakeClock())
        store.create_entry(quote="q1", response="r1", session="gemini")
        store.create_entry(quote="q2", response="r2")  # general: must NOT appear
        store.create_entry(quote="q3", response="r3", session="gemini")

        # Act
        payload = store.assemble_session("gemini")

        # Assert: historical numbers preserved, only that session's entries
        assert payload == '1. "q1"\n: r1\n\n3. "q3"\n: r3'
        assert store.assemble_session("general") == '2. "q2"\n: r2'
        assert store.assemble_session("sin-entradas") == ""

    def test_migration_entries_without_session_become_general(self, tmp_path):
        # Arrange: pre-REQ-2 JSON has no ``session`` field at all
        path = tmp_path / "entries.json"
        path.write_text(
            json.dumps(
                {
                    "version": 1,
                    "next_number": 3,
                    "entries": [
                        {"number": 1, "response": "legacy"},
                        {"number": 2, "session": "claude", "response": "ya etiquetada"},
                    ],
                }
            ),
            encoding="utf-8",
        )

        # Act
        store = SupervisorStore(path, now_fn=_FakeClock())

        # Assert: missing -> "general" (backward compatible), existing preserved
        assert store.get(1).session == "general"
        assert store.get(2).session == "claude"

    def test_migration_persists_session_field_on_next_save(self, tmp_path):
        # Arrange: legacy file without ``session`` anywhere
        path = tmp_path / "entries.json"
        path.write_text(json.dumps({"version": 1, "entries": [{"number": 1}]}), encoding="utf-8")
        store = SupervisorStore(path, now_fn=_FakeClock())

        # Act: any mutation rewrites the whole file
        store.create_entry(response="nueva")

        # Assert: both the migrated and the fresh entry carry a session
        payload = json.loads(path.read_text(encoding="utf-8"))
        assert payload["entries"][0]["session"] == "general"
        assert payload["entries"][1]["session"] == "general"

    def test_roundtrip_preserves_session(self):
        # Arrange
        entry = SupervisorEntry(number=5, quote="q", response="r", session="agente-x")

        # Act
        restored = supervisor_store._entry_from_dict(supervisor_store._entry_to_dict(entry))

        # Assert
        assert restored == entry
