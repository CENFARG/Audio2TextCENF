"""@File: audio2text/services/history_service.py
@Description: HistoryService — transcription history management with legacy migration.
@Version: 0.16.0
@Author: CENF Development Team
@License: Apache-2.0
"""

from __future__ import annotations

import datetime
import json
import logging
import uuid
from pathlib import Path

from audio2text.domain.metadata import TranscriptionMetadata
from audio2text.services.metadata_service import MetadataService

logger = logging.getLogger(__name__)


class HistoryService:
    """Manages transcription history with migration from legacy JSONL format.

    Wraps ``MetadataService`` for CRUD and adds:
        - ``load_history()`` — read old-style JSONL files into ``TranscriptionMetadata``.
        - ``migrate()`` — convert old JSONL to new MetadataService storage.
        - ``save_history()`` — batch-persist entries via MetadataService.
        - ``list_all()`` / ``delete()`` — delegation to MetadataService.
    """

    def __init__(
        self,
        metadata_service: MetadataService | None = None,
    ) -> None:
        """Initialize the history service.

        Args:
            metadata_service: An existing ``MetadataService`` instance.
                              If None, creates a default one.
        """
        self._metadata_service = metadata_service or MetadataService()

    # ------------------------------------------------------------------
    # Migration from old format
    # ------------------------------------------------------------------

    def load_history(self, jsonl_path: Path) -> list[TranscriptionMetadata]:
        """Read an old-style JSONL history file and convert entries.

        Old format (v0.15):
            {"filename": "...", "text": "...", "timestamp": "YYYY-MM-DDTHH:MM:SS", ...}

        Returns a list of ``TranscriptionMetadata`` instances.
        Corrupted lines are skipped with a warning.

        Args:
            jsonl_path: Path to the old JSONL file.

        Returns:
            List of TranscriptionMetadata entries. Empty if file doesn't exist.
        """
        if not jsonl_path.exists():
            return []

        entries: list[TranscriptionMetadata] = []
        for line_num, line in enumerate(
            jsonl_path.read_text(encoding="utf-8").splitlines(), start=1
        ):
            stripped = line.strip()
            if not stripped:
                continue
            parsed = self._parse_old_entry(stripped, line_num)
            if parsed is not None:
                entries.append(parsed)

        return entries

    def migrate(self, old_jsonl_path: Path) -> int:
        """Migrate old JSONL history to MetadataService storage.

        Args:
            old_jsonl_path: Path to the old JSONL file.

        Returns:
            Number of entries migrated.
        """
        entries = self.load_history(old_jsonl_path)
        self.save_history(entries)
        return len(entries)

    # ------------------------------------------------------------------
    # New format operations (delegate to MetadataService)
    # ------------------------------------------------------------------

    def save_history(self, entries: list[TranscriptionMetadata]) -> None:
        """Persist multiple entries via MetadataService.

        Args:
            entries: TranscriptionMetadata entries to save.
        """
        for entry in entries:
            self._metadata_service.save(entry)

    def list_all(self) -> list[TranscriptionMetadata]:
        """List all history entries.

        Returns:
            All TranscriptionMetadata entries.
        """
        return self._metadata_service.list_all()

    def delete(self, metadata_id: str) -> bool:
        """Delete a history entry by ID.

        Args:
            metadata_id: The entry ID to delete.

        Returns:
            True if deleted, False if not found.
        """
        return self._metadata_service.delete(metadata_id)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_old_entry(
        line: str, line_num: int
    ) -> TranscriptionMetadata | None:
        """Parse a single old JSONL line into TranscriptionMetadata.

        Args:
            line: Raw JSON line from old JSONL file.
            line_num: Line number for error reporting.

        Returns:
            TranscriptionMetadata or None if parsing failed.
        """
        try:
            raw = json.loads(line)
        except json.JSONDecodeError:
            logger.warning("Skipping corrupted history line %d (invalid JSON)", line_num)
            return None

        filename = raw.get("filename", f"unknown_{line_num}")
        text = raw.get("text", "")
        ts_str = raw.get("timestamp", "")

        # Parse timestamp
        created_at = datetime.datetime.now(datetime.timezone.utc)
        if ts_str:
            try:
                created_at = datetime.datetime.fromisoformat(ts_str)
                if created_at.tzinfo is None:
                    created_at = created_at.replace(tzinfo=datetime.timezone.utc)
            except (ValueError, TypeError):
                logger.warning(
                    "Invalid timestamp on history line %d: '%s'", line_num, ts_str
                )

        # Generate a new ID (old entries didn't have structured IDs)
        entry_id = f"hist-{uuid.uuid4().hex[:8]}"

        return TranscriptionMetadata(
            id=entry_id,
            filename=filename,
            title=text[:100] if text else filename,
            created_at=created_at,
        )
