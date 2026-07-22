"""
MetadataProvider Protocol — contract for transcription metadata storage.

Adapters (JSONL, database) satisfy this Protocol.
Injected into TranscriptionService for history/metadata persistence.
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from audio2text.domain.metadata import TranscriptionMetadata


@runtime_checkable
class MetadataProvider(Protocol):
    """Structural contract for metadata persistence backends."""

    def save(self, metadata: TranscriptionMetadata) -> None:
        """Persist a transcription metadata record."""
        ...

    def list(self, limit: int = 100) -> list[TranscriptionMetadata]:
        """List recent metadata records."""
        ...

    def get(self, transcription_id: str) -> TranscriptionMetadata | None:
        """Retrieve a metadata record by ID."""
        ...