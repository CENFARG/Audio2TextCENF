"""@File: audio2text/domain/metadata.py
@Description: Transcription metadata domain model.
@Version: 0.16.0
@Author: CENF Development Team
@License: Apache-2.0
"""

from __future__ import annotations

import datetime
from dataclasses import dataclass, field


@dataclass
class TranscriptionMetadata:
    """Metadata associated with a transcription.

    Attributes:
        id: Unique identifier for this transcription.
        filename: Original audio filename.
        emoji: Optional emoji representing the transcription topic.
        title: Human-readable title.
        tags: List of tags for categorization.
        notes: Free-form notes.
        created_at: UTC timestamp when the transcription was created.
        audio_path: File path to the source audio.
    """

    id: str
    filename: str
    emoji: str | None = None
    title: str | None = None
    tags: list[str] = field(default_factory=list)
    notes: str | None = None
    created_at: datetime.datetime = field(
        default_factory=lambda: datetime.datetime.now(datetime.timezone.utc)
    )
    audio_path: str | None = None

    def __eq__(self, other: object) -> bool:
        """Two metadata instances are equal if they share the same id."""
        if not isinstance(other, TranscriptionMetadata):
            return NotImplemented
        return self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)
