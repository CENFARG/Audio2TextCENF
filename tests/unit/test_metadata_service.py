"""@File: tests/unit/test_metadata_service.py
@Description: Unit tests for MetadataService (Task 3.3b). TDD cycle — RED first.
@Version: 0.16.0
@Author: CENF Development Team
@License: Apache-2.0
"""

from __future__ import annotations

import tempfile
from pathlib import Path


class TestMetadataServiceInit:
    """Tests for MetadataService initialization."""

    def test_create_with_storage_dir(self) -> None:
        """Service can be created with a storage directory."""
        from audio2text.services.metadata_service import MetadataService

        with tempfile.TemporaryDirectory() as tmp:
            service = MetadataService(storage_dir=Path(tmp))
            assert service is not None


class TestMetadataServiceCRUD:
    """Tests for create, read, update, delete operations."""

    def test_save_and_get_metadata(self) -> None:
        """Metadata can be saved and retrieved by ID."""
        from audio2text.domain.metadata import TranscriptionMetadata
        from audio2text.services.metadata_service import MetadataService

        with tempfile.TemporaryDirectory() as tmp:
            service = MetadataService(storage_dir=Path(tmp))
            meta = TranscriptionMetadata(
                id="test-001",
                filename="recording.wav",
                title="Test recording",
                tags=["test"],
            )
            service.save(meta)
            retrieved = service.get("test-001")

        assert retrieved is not None
        assert retrieved.id == "test-001"
        assert retrieved.title == "Test recording"

    def test_get_nonexistent_returns_none(self) -> None:
        """Getting a nonexistent ID returns None."""
        from audio2text.services.metadata_service import MetadataService

        with tempfile.TemporaryDirectory() as tmp:
            service = MetadataService(storage_dir=Path(tmp))
            retrieved = service.get("nonexistent")

        assert retrieved is None

    def test_update_metadata(self) -> None:
        """Update modifies existing metadata fields."""
        from audio2text.domain.metadata import TranscriptionMetadata
        from audio2text.services.metadata_service import MetadataService

        with tempfile.TemporaryDirectory() as tmp:
            service = MetadataService(storage_dir=Path(tmp))
            meta = TranscriptionMetadata(id="test-002", filename="rec.wav")
            service.save(meta)

            # Update title
            updated = service.update("test-002", title="Nuevo título", emoji="🎤")
            assert updated is not None
            assert updated.title == "Nuevo título"
            assert updated.emoji == "🎤"

    def test_delete_metadata(self) -> None:
        """Delete removes a metadata entry."""
        from audio2text.domain.metadata import TranscriptionMetadata
        from audio2text.services.metadata_service import MetadataService

        with tempfile.TemporaryDirectory() as tmp:
            service = MetadataService(storage_dir=Path(tmp))
            meta = TranscriptionMetadata(id="test-003", filename="rec.wav")
            service.save(meta)
            assert service.delete("test-003") is True
            assert service.get("test-003") is None

    def test_delete_nonexistent_returns_false(self) -> None:
        """Deleting a nonexistent ID returns False."""
        from audio2text.services.metadata_service import MetadataService

        with tempfile.TemporaryDirectory() as tmp:
            service = MetadataService(storage_dir=Path(tmp))
            assert service.delete("nonexistent") is False

    def test_list_all(self) -> None:
        """list_all() returns all saved metadata."""
        from audio2text.domain.metadata import TranscriptionMetadata
        from audio2text.services.metadata_service import MetadataService

        with tempfile.TemporaryDirectory() as tmp:
            service = MetadataService(storage_dir=Path(tmp))
            service.save(TranscriptionMetadata(id="a", filename="a.wav"))
            service.save(TranscriptionMetadata(id="b", filename="b.wav"))

            all_meta = service.list_all()
            assert len(all_meta) == 2


class TestMetadataServiceSearch:
    """Tests for search/filter functionality."""

    def test_search_by_tag(self) -> None:
        """search() can filter by tag."""
        from audio2text.domain.metadata import TranscriptionMetadata
        from audio2text.services.metadata_service import MetadataService

        with tempfile.TemporaryDirectory() as tmp:
            service = MetadataService(storage_dir=Path(tmp))
            service.save(
                TranscriptionMetadata(
                    id="a", filename="a.wav", tags=["reunion", "importante"]
                )
            )
            service.save(
                TranscriptionMetadata(
                    id="b", filename="b.wav", tags=["personal"]
                )
            )

            results = service.search(tag="reunion")
            assert len(results) == 1
            assert results[0].id == "a"

    def test_search_by_title(self) -> None:
        """search() can filter by title substring."""
        from audio2text.domain.metadata import TranscriptionMetadata
        from audio2text.services.metadata_service import MetadataService

        with tempfile.TemporaryDirectory() as tmp:
            service = MetadataService(storage_dir=Path(tmp))
            service.save(TranscriptionMetadata(id="a", filename="a.wav", title="Reunión semanal"))
            service.save(TranscriptionMetadata(id="b", filename="b.wav", title="Notas personales"))

            results = service.search(query="reunión")
            assert len(results) == 1
            assert results[0].id == "a"

    def test_search_no_match_returns_empty(self) -> None:
        """search() returns empty list when nothing matches."""
        from audio2text.services.metadata_service import MetadataService

        with tempfile.TemporaryDirectory() as tmp:
            service = MetadataService(storage_dir=Path(tmp))
            results = service.search(query="nada")
            assert results == []
