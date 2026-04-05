"""
Unit tests for TranscriptionMetadata class.

This module tests metadata management functionality including:
- Emoji management
- Title management
- Tag management
- Notes management
- Auto-metadata (LLM-generated)
- Metadata persistence

Author: Audio2Text Development Team
Version: 0.13.0
"""

import pytest
import sys
import os
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.transcription_metadata import TranscriptionMetadata


@pytest.mark.unit
class TestTranscriptionMetadataInitialization:
    """Tests for TranscriptionMetadata initialization."""

    def test_initialization_creates_new_file(self):
        """Test initialization creates new metadata file if it doesn't exist."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            metadata_file = f.name

        try:
            # Delete file to test creation
            if os.path.exists(metadata_file):
                os.unlink(metadata_file)

            metadata = TranscriptionMetadata(metadata_file=metadata_file)

            assert metadata.metadata == {}
            assert metadata.metadata_file == metadata_file
        finally:
            if os.path.exists(metadata_file):
                os.unlink(metadata_file)

    def test_initialization_loads_existing_file(self):
        """Test initialization loads existing metadata file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            metadata_file = f.name
            test_data = {"audio_1.wav": {"emoji": "🎤", "title": "Test Title"}}
            json.dump(test_data, f)

        try:
            metadata = TranscriptionMetadata(metadata_file=metadata_file)

            assert metadata.metadata == test_data
            assert metadata.get_emoji("audio_1.wav") == "🎤"
        finally:
            if os.path.exists(metadata_file):
                os.unlink(metadata_file)

    def test_initialization_handles_corrupt_file(self):
        """Test initialization handles corrupted file gracefully."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            metadata_file = f.name
            f.write("invalid json content")

        try:
            metadata = TranscriptionMetadata(metadata_file=metadata_file)

            # Should default to empty dict
            assert metadata.metadata == {}
        finally:
            if os.path.exists(metadata_file):
                os.unlink(metadata_file)


@pytest.mark.unit
class TestEmojiManagement:
    """Tests for emoji management."""

    @pytest.fixture
    def metadata(self):
        """Create a TranscriptionMetadata instance."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            metadata_file = f.name

        metadata = TranscriptionMetadata(metadata_file=metadata_file)
        yield metadata

        if os.path.exists(metadata_file):
            os.unlink(metadata_file)

    def test_get_emoji_default(self, metadata):
        """Test getting default emoji when none set."""
        emoji = metadata.get_emoji("audio_1.wav")
        assert emoji == "🎤"

    def test_get_emoji_custom_default(self, metadata):
        """Test getting custom default emoji."""
        emoji = metadata.get_emoji("audio_1.wav", default="📝")
        assert emoji == "📝"

    def test_set_emoji(self, metadata):
        """Test setting emoji for a file."""
        metadata.set_emoji("audio_1.wav", "🎵")

        emoji = metadata.get_emoji("audio_1.wav")
        assert emoji == "🎵"

    def test_set_emoji_persists(self, metadata):
        """Test that emoji is persisted to file."""
        metadata.set_emoji("audio_2.wav", "🎸")

        # Create new instance to test persistence
        metadata2 = TranscriptionMetadata(metadata_file=metadata.metadata_file)
        emoji = metadata2.get_emoji("audio_2.wav")

        assert emoji == "🎸"

    def test_update_emoji(self, metadata):
        """Test updating existing emoji."""
        metadata.set_emoji("audio_1.wav", "🎤")
        metadata.set_emoji("audio_1.wav", "🎹")

        emoji = metadata.get_emoji("audio_1.wav")
        assert emoji == "🎹"


@pytest.mark.unit
class TestTitleManagement:
    """Tests for title management."""

    @pytest.fixture
    def metadata(self):
        """Create a TranscriptionMetadata instance."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            metadata_file = f.name

        metadata = TranscriptionMetadata(metadata_file=metadata_file)
        yield metadata

        if os.path.exists(metadata_file):
            os.unlink(metadata_file)

    def test_get_title_default(self, metadata):
        """Test getting default title when none set."""
        title = metadata.get_title("audio_1.wav")
        assert title is None

    def test_get_title_custom_default(self, metadata):
        """Test getting custom default title."""
        title = metadata.get_title("audio_1.wav", default="Audio 1")
        assert title == "Audio 1"

    def test_set_title(self, metadata):
        """Test setting title for a file."""
        metadata.set_title("audio_1.wav", "My Recording")

        title = metadata.get_title("audio_1.wav")
        assert title == "My Recording"

    def test_set_title_persists(self, metadata):
        """Test that title is persisted to file."""
        metadata.set_title("audio_2.wav", "Persisted Title")

        # Create new instance
        metadata2 = TranscriptionMetadata(metadata_file=metadata.metadata_file)
        title = metadata2.get_title("audio_2.wav")

        assert title == "Persisted Title"


@pytest.mark.unit
class TestTagManagement:
    """Tests for tag management."""

    @pytest.fixture
    def metadata(self):
        """Create a TranscriptionMetadata instance."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            metadata_file = f.name

        metadata = TranscriptionMetadata(metadata_file=metadata_file)
        yield metadata

        if os.path.exists(metadata_file):
            os.unlink(metadata_file)

    def test_get_tags_default(self, metadata):
        """Test getting tags when none set."""
        tags = metadata.get_tags("audio_1.wav")
        assert tags == []

    def test_set_tags(self, metadata):
        """Test setting tags for a file."""
        tags = ["important", "work", "meeting"]
        metadata.set_tags("audio_1.wav", tags)

        result = metadata.get_tags("audio_1.wav")
        assert result == tags

    def test_set_tags_persists(self, metadata):
        """Test that tags are persisted."""
        tags = ["test", "demo"]
        metadata.set_tags("audio_2.wav", tags)

        # Create new instance
        metadata2 = TranscriptionMetadata(metadata_file=metadata.metadata_file)
        result = metadata2.get_tags("audio_2.wav")

        assert result == tags

    def test_update_tags(self, metadata):
        """Test updating existing tags."""
        metadata.set_tags("audio_1.wav", ["tag1", "tag2"])
        metadata.set_tags("audio_1.wav", ["tag3", "tag4"])

        result = metadata.get_tags("audio_1.wav")
        assert result == ["tag3", "tag4"]


@pytest.mark.unit
class TestNotesManagement:
    """Tests for notes management."""

    @pytest.fixture
    def metadata(self):
        """Create a TranscriptionMetadata instance."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            metadata_file = f.name

        metadata = TranscriptionMetadata(metadata_file=metadata_file)
        yield metadata

        if os.path.exists(metadata_file):
            os.unlink(metadata_file)

    def test_get_notes_default(self, metadata):
        """Test getting notes when none set."""
        notes = metadata.get_notes("audio_1.wav")
        assert notes is None

    def test_set_notes(self, metadata):
        """Test setting notes for a file."""
        notes = "These are important notes about the recording."
        metadata.set_notes("audio_1.wav", notes)

        result = metadata.get_notes("audio_1.wav")
        assert result == notes

    def test_set_notes_persists(self, metadata):
        """Test that notes are persisted."""
        notes = "Persisted notes"
        metadata.set_notes("audio_2.wav", notes)

        # Create new instance
        metadata2 = TranscriptionMetadata(metadata_file=metadata.metadata_file)
        result = metadata2.get_notes("audio_2.wav")

        assert result == notes


@pytest.mark.unit
class TestAutoMetadata:
    """Tests for auto-generated metadata (LLM)."""

    @pytest.fixture
    def metadata(self):
        """Create a TranscriptionMetadata instance."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            metadata_file = f.name

        metadata = TranscriptionMetadata(metadata_file=metadata_file)
        yield metadata

        if os.path.exists(metadata_file):
            os.unlink(metadata_file)

    def test_set_auto_metadata(self, metadata):
        """Test setting auto-generated metadata."""
        auto_meta = {
            "summary": "This is a summary",
            "tasks": ["Task 1", "Task 2"],
            "keywords": ["keyword1", "keyword2"],
            "category": "Work",
        }

        metadata.set_auto_metadata("audio_1.wav", auto_meta)

        result = metadata.get_auto_metadata("audio_1.wav")
        assert result == auto_meta

    def test_get_auto_metadata_default(self, metadata):
        """Test getting auto-metadata when none set."""
        result = metadata.get_auto_metadata("audio_1.wav")
        assert result == {}

    def test_auto_metadata_persists(self, metadata):
        """Test that auto-metadata is persisted."""
        auto_meta = {"summary": "Test summary", "category": "Test"}
        metadata.set_auto_metadata("audio_2.wav", auto_meta)

        # Create new instance
        metadata2 = TranscriptionMetadata(metadata_file=metadata.metadata_file)
        result = metadata2.get_auto_metadata("audio_2.wav")

        assert result == auto_meta


@pytest.mark.unit
class TestMetadataOperations:
    """Tests for general metadata operations."""

    @pytest.fixture
    def metadata(self):
        """Create a TranscriptionMetadata instance."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            metadata_file = f.name

        metadata = TranscriptionMetadata(metadata_file=metadata_file)
        yield metadata

        if os.path.exists(metadata_file):
            os.unlink(metadata_file)

    def test_get_all_metadata(self, metadata):
        """Test getting all metadata for a file."""
        metadata.set_emoji("audio_1.wav", "🎤")
        metadata.set_title("audio_1.wav", "Test Title")
        metadata.set_tags("audio_1.wav", ["tag1"])

        result = metadata.get_all_metadata("audio_1.wav")

        assert result["emoji"] == "🎤"
        assert result["title"] == "Test Title"
        assert result["tags"] == ["tag1"]

    def test_get_all_metadata_empty(self, metadata):
        """Test getting all metadata when none exists."""
        result = metadata.get_all_metadata("audio_1.wav")
        assert result == {}

    def test_delete_metadata(self, metadata):
        """Test deleting metadata for a file."""
        metadata.set_emoji("audio_1.wav", "🎤")
        metadata.set_title("audio_1.wav", "Title")

        metadata.delete_metadata("audio_1.wav")

        result = metadata.get_all_metadata("audio_1.wav")
        assert result == {}

    def test_delete_nonexistent_metadata(self, metadata):
        """Test deleting metadata for non-existent file (should not crash)."""
        # Should not raise exception
        metadata.delete_metadata("nonexistent.wav")

    def test_clear_all(self, metadata):
        """Test clearing all metadata."""
        metadata.set_emoji("audio_1.wav", "🎤")
        metadata.set_title("audio_2.wav", "Title")

        metadata.clear_all()

        assert metadata.metadata == {}

    def test_get_display_name_with_emoji(self, metadata):
        """Test getting display name with emoji."""
        metadata.set_emoji("audio_1.wav", "🎤")
        metadata.set_title("audio_1.wav", "My Recording")

        display = metadata.get_display_name("audio_1.wav", include_emoji=True)

        assert "🎤" in display
        assert "My Recording" in display

    def test_get_display_name_without_emoji(self, metadata):
        """Test getting display name without emoji."""
        metadata.set_title("audio_1.wav", "My Recording")

        display = metadata.get_display_name("audio_1.wav", include_emoji=False)

        assert "My Recording" in display
        assert display == "My Recording"

    def test_get_display_name_fallback_to_filename(self, metadata):
        """Test display name falls back to filename if no title."""
        display = metadata.get_display_name("audio_1.wav")

        assert display == "audio_1.wav"


@pytest.mark.unit
class TestMetadataPersistence:
    """Tests for metadata persistence and file I/O."""

    @pytest.fixture
    def metadata(self):
        """Create a TranscriptionMetadata instance."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            metadata_file = f.name

        metadata = TranscriptionMetadata(metadata_file=metadata_file)
        yield metadata

        if os.path.exists(metadata_file):
            os.unlink(metadata_file)

    def test_multiple_operations_persist(self, metadata):
        """Test that multiple operations persist correctly."""
        # Set various metadata
        metadata.set_emoji("audio_1.wav", "🎤")
        metadata.set_title("audio_1.wav", "Title 1")
        metadata.set_tags("audio_1.wav", ["tag1"])

        metadata.set_emoji("audio_2.wav", "🎹")
        metadata.set_title("audio_2.wav", "Title 2")

        # Create new instance
        metadata2 = TranscriptionMetadata(metadata_file=metadata.metadata_file)

        # Verify all persisted
        assert metadata2.get_emoji("audio_1.wav") == "🎤"
        assert metadata2.get_title("audio_1.wav") == "Title 1"
        assert metadata2.get_tags("audio_1.wav") == ["tag1"]
        assert metadata2.get_emoji("audio_2.wav") == "🎹"
        assert metadata2.get_title("audio_2.wav") == "Title 2"

    def test_concurrent_access(self, metadata):
        """Test that concurrent access (simulation) works."""
        # Simulate multiple updates
        for i in range(10):
            metadata.set_emoji(f"audio_{i}.wav", f"emoji_{i}")

        # Verify all persisted
        metadata2 = TranscriptionMetadata(metadata_file=metadata.metadata_file)
        assert len(metadata2.metadata) == 10
