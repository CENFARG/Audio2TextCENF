"""@File: tests/unit/test_history_service.py
@Description: Unit tests for HistoryService — history migration and management.
@Version: 0.16.0
@Author: CENF Development Team
@License: Apache-2.0
"""

from __future__ import annotations

import datetime
import json
from pathlib import Path

from audio2text.domain.metadata import TranscriptionMetadata

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_old_jsonl_entry(
    filename: str = "recording_2026-05-12.wav",
    text: str = "Old transcription text",
    timestamp: str | None = None,
) -> dict:
    """Build an old-style JSONL entry (flat dict)."""
    ts = timestamp or "2026-05-12T15:30:00"
    return {
        "filename": filename,
        "text": text,
        "timestamp": ts,
        "language": "es",
        "duration": 45.2,
    }


def _make_old_jsonl_file(path: Path, entries: list[dict]) -> None:
    """Write old-style JSONL entries to a file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(str(path), "w", encoding="utf-8") as f:
        for entry in entries:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")


# ---------------------------------------------------------------------------
# RED phase — HistoryService does not exist yet
# ---------------------------------------------------------------------------


class TestHistoryService:
    """Unit tests for HistoryService (migration + load/save)."""

    def test_load_history_reads_old_jsonl(self, tmp_path: Path) -> None:
        """Given an old-style JSONL file, load_history returns TranscriptionMetadata list."""
        from audio2text.services.history_service import HistoryService

        old_file = tmp_path / "old_history.jsonl"
        _make_old_jsonl_file(old_file, [
            _make_old_jsonl_entry(filename="rec1.wav", text="First transcription"),
            _make_old_jsonl_entry(filename="rec2.wav", text="Second transcription"),
        ])

        service = HistoryService()
        results = service.load_history(old_file)

        assert len(results) == 2
        assert isinstance(results[0], TranscriptionMetadata)
        assert results[0].filename == "rec1.wav"
        assert results[1].filename == "rec2.wav"

    def test_load_history_returns_empty_for_missing_file(self, tmp_path: Path) -> None:
        """When the history file does not exist, load returns an empty list."""
        from audio2text.services.history_service import HistoryService

        service = HistoryService()
        results = service.load_history(tmp_path / "nonexistent.jsonl")
        assert results == []

    def test_load_history_skips_corrupted_lines(self, tmp_path: Path) -> None:
        """Corrupted JSONL lines are skipped, valid ones are loaded."""
        from audio2text.services.history_service import HistoryService

        old_file = tmp_path / "mixed.jsonl"
        old_file.parent.mkdir(parents=True, exist_ok=True)
        with open(str(old_file), "w", encoding="utf-8") as f:
            f.write(json.dumps(_make_old_jsonl_entry(filename="good.wav", text="Good")) + "\n")
            f.write("this is not valid json\n")
            f.write(json.dumps(_make_old_jsonl_entry(filename="also_good.wav", text="Also good")) + "\n")

        service = HistoryService()
        results = service.load_history(old_file)

        assert len(results) == 2
        assert results[0].filename == "good.wav"
        assert results[1].filename == "also_good.wav"

    def test_save_history_persists_via_metadata_service(self, tmp_path: Path) -> None:
        """save_history writes entries through MetadataService."""
        from audio2text.services.history_service import HistoryService
        from audio2text.services.metadata_service import MetadataService

        meta_service = MetadataService(storage_dir=tmp_path / "metadata")
        history_service = HistoryService(metadata_service=meta_service)

        entries = [
            TranscriptionMetadata(
                id="hist-001",
                filename="saved1.wav",
                title="Saved transcription 1",
                created_at=datetime.datetime(2026, 5, 12, 10, 0, 0, tzinfo=datetime.timezone.utc),
            ),
            TranscriptionMetadata(
                id="hist-002",
                filename="saved2.wav",
                title="Saved transcription 2",
                created_at=datetime.datetime(2026, 5, 12, 11, 0, 0, tzinfo=datetime.timezone.utc),
            ),
        ]

        history_service.save_history(entries)

        # Verify via MetadataService
        all_meta = meta_service.list_all()
        assert len(all_meta) == 2
        assert all_meta[0].id == "hist-001"
        assert all_meta[1].id == "hist-002"

    def test_migrate_converts_old_to_new_and_saves(
        self, tmp_path: Path
    ) -> None:
        """Full migration: old JSONL → MetadataService."""
        from audio2text.services.history_service import HistoryService
        from audio2text.services.metadata_service import MetadataService

        old_file = tmp_path / "old_history.jsonl"
        _make_old_jsonl_file(old_file, [
            _make_old_jsonl_entry(filename="migrate1.wav", text="Will be migrated 1"),
            _make_old_jsonl_entry(filename="migrate2.wav", text="Will be migrated 2"),
        ])

        meta_service = MetadataService(storage_dir=tmp_path / "metadata")
        history_service = HistoryService(metadata_service=meta_service)

        count = history_service.migrate(old_file)

        assert count == 2
        all_meta = meta_service.list_all()
        assert len(all_meta) == 2
        assert all(s.filename in ("migrate1.wav", "migrate2.wav") for s in all_meta)

    def test_list_all_delegates_to_metadata_service(self, tmp_path: Path) -> None:
        """list_all returns all entries via MetadataService."""
        from audio2text.services.history_service import HistoryService
        from audio2text.services.metadata_service import MetadataService

        meta_service = MetadataService(storage_dir=tmp_path / "metadata")
        # Pre-populate some entries
        meta_service.save(TranscriptionMetadata(
            id="list-001", filename="a.wav",
            created_at=datetime.datetime(2026, 5, 12, tzinfo=datetime.timezone.utc),
        ))
        meta_service.save(TranscriptionMetadata(
            id="list-002", filename="b.wav",
            created_at=datetime.datetime(2026, 5, 12, tzinfo=datetime.timezone.utc),
        ))

        history_service = HistoryService(metadata_service=meta_service)
        results = history_service.list_all()

        assert len(results) == 2
        assert {r.id for r in results} == {"list-001", "list-002"}

    def test_delete_entry_delegates_to_metadata_service(self, tmp_path: Path) -> None:
        """delete removes an entry via MetadataService."""
        from audio2text.services.history_service import HistoryService
        from audio2text.services.metadata_service import MetadataService

        meta_service = MetadataService(storage_dir=tmp_path / "metadata")
        meta_service.save(TranscriptionMetadata(
            id="del-001", filename="to_delete.wav",
            created_at=datetime.datetime(2026, 5, 12, tzinfo=datetime.timezone.utc),
        ))

        history_service = HistoryService(metadata_service=meta_service)

        assert history_service.delete("del-001") is True
        assert meta_service.get("del-001") is None

    def test_delete_nonexistent_returns_false(self, tmp_path: Path) -> None:
        """Deleting a non-existent entry returns False."""
        from audio2text.services.history_service import HistoryService
        from audio2text.services.metadata_service import MetadataService

        meta_service = MetadataService(storage_dir=tmp_path / "metadata")
        history_service = HistoryService(metadata_service=meta_service)

        assert history_service.delete("nonexistent") is False
