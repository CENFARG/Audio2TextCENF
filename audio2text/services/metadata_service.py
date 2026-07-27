"""@File: audio2text/services/metadata_service.py
@Description: MetadataService — CRUD operations for transcription metadata.
    Supports emoji assignment, title editing, tags, notes, and search/filter.
@Version: 0.16.0
@Author: CENF Development Team
@License: Apache-2.0
"""

from __future__ import annotations

import datetime
import json
from pathlib import Path

from audio2text.domain.metadata import TranscriptionMetadata


class MetadataService:
    """Persistent storage and retrieval of transcription metadata.

    Provides CRUD operations (create, read, update, delete) and search
    functionality for ``TranscriptionMetadata`` instances. Data is stored
    as JSON files in the configured storage directory, one file per ID.
    """

    def __init__(self, storage_dir: Path | str = "transcriptions") -> None:
        """Initialize the metadata service.

        Args:
            storage_dir: Directory where metadata JSON files are stored.
                         Created automatically if it does not exist.
        """
        self._storage_dir = Path(storage_dir)
        self._storage_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Public API — CRUD
    # ------------------------------------------------------------------

    def save(self, metadata: TranscriptionMetadata) -> None:
        """Persist a metadata entry.

        Args:
            metadata: The TranscriptionMetadata to save.
        """
        file_path = self._path_for(metadata.id)
        data = self._serialize(metadata)
        file_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def get(self, metadata_id: str) -> TranscriptionMetadata | None:
        """Retrieve a metadata entry by ID.

        Args:
            metadata_id: The unique identifier.

        Returns:
            The TranscriptionMetadata if found, or None.
        """
        file_path = self._path_for(metadata_id)
        if not file_path.exists():
            return None
        return self._deserialize(file_path.read_text(encoding="utf-8"))

    def update(self, metadata_id: str, **fields: object) -> TranscriptionMetadata | None:
        """Update fields of an existing metadata entry.

        Args:
            metadata_id: The unique identifier.
            **fields: Keyword arguments mapping field names to new values.
                      Supported: title, emoji, tags, notes.

        Returns:
            The updated TranscriptionMetadata if found, or None.
        """
        existing = self.get(metadata_id)
        if existing is None:
            return None

        if "title" in fields:
            existing.title = str(fields["title"]) if fields["title"] is not None else None
        if "emoji" in fields:
            existing.emoji = str(fields["emoji"]) if fields["emoji"] is not None else None
        if "tags" in fields and isinstance(fields["tags"], list):
            existing.tags = [str(t) for t in fields["tags"]]
        if "notes" in fields:
            existing.notes = str(fields["notes"]) if fields["notes"] is not None else None

        self.save(existing)
        return existing

    def delete(self, metadata_id: str) -> bool:
        """Delete a metadata entry.

        Args:
            metadata_id: The unique identifier.

        Returns:
            True if the entry was deleted, False if it didn't exist.
        """
        file_path = self._path_for(metadata_id)
        if not file_path.exists():
            return False
        file_path.unlink()
        return True

    def list_all(self) -> list[TranscriptionMetadata]:
        """Return all saved metadata entries.

        Returns:
            A list of TranscriptionMetadata objects.
        """
        results: list[TranscriptionMetadata] = []
        for json_file in sorted(self._storage_dir.glob("*.json")):
            metadata = self._deserialize(json_file.read_text(encoding="utf-8"))
            if metadata is not None:
                results.append(metadata)
        return results

    # ------------------------------------------------------------------
    # Public API — search
    # ------------------------------------------------------------------

    def search(
        self,
        query: str | None = None,
        tag: str | None = None,
    ) -> list[TranscriptionMetadata]:
        """Search metadata entries by title substring and/or tag.

        Args:
            query: Substring to match in the title (case-insensitive).
            tag: Exact tag to match.

        Returns:
            Matching TranscriptionMetadata entries.
        """
        results: list[TranscriptionMetadata] = []
        for entry in self.list_all():
            if query and query.lower() not in (entry.title or "").lower():
                continue
            if tag and tag not in entry.tags:
                continue
            results.append(entry)
        return results

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _path_for(self, metadata_id: str) -> Path:
        """Get the file path for a given metadata ID."""
        safe_id = "".join(
            c for c in metadata_id if c.isalnum() or c in "-_."
        )
        return self._storage_dir / f"{safe_id}.json"

    @staticmethod
    def _serialize(metadata: TranscriptionMetadata) -> dict[str, object]:
        """Convert a TranscriptionMetadata to a JSON-safe dict."""
        return {
            "id": metadata.id,
            "filename": metadata.filename,
            "emoji": metadata.emoji,
            "title": metadata.title,
            "tags": metadata.tags,
            "notes": metadata.notes,
            "created_at": metadata.created_at.isoformat(),
            "audio_path": metadata.audio_path,
        }

    @staticmethod
    def _deserialize(data: str) -> TranscriptionMetadata | None:
        """Parse a JSON string into TranscriptionMetadata.

        Returns None if parsing fails.
        """
        try:
            raw = json.loads(data)
            return TranscriptionMetadata(
                id=raw["id"],
                filename=raw["filename"],
                emoji=raw.get("emoji"),
                title=raw.get("title"),
                tags=raw.get("tags", []),
                notes=raw.get("notes"),
                created_at=datetime.datetime.fromisoformat(raw["created_at"])
                if "created_at" in raw
                else datetime.datetime.now(datetime.timezone.utc),
                audio_path=raw.get("audio_path"),
            )
        except (json.JSONDecodeError, KeyError, TypeError):
            return None
