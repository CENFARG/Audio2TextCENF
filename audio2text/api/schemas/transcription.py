"""@File: audio2text/api/schemas/transcription.py
@Description: Pydantic schemas for transcription requests and responses.
@Version: 0.16.0
@Author: CENF Development Team
@License: Apache-2.0
"""

from __future__ import annotations

import datetime
from typing import Any

from pydantic import BaseModel, Field


class TranscriptionResponse(BaseModel):
    """Response body for a completed transcription.

    Attributes:
        id: Unique transcription identifier.
        text: The transcribed text.
        language: Language code (e.g., "es", "en").
        provider: Transcription provider name.
        model: Model name used for transcription.
        duration_s: Duration of the source audio in seconds.
        segments: Optional list of timestamped segments.
        created_at: UTC timestamp when the transcription was created.
    """

    id: str
    text: str
    language: str
    provider: str
    model: str
    duration_s: float
    segments: list[dict[str, Any]] | None = None
    created_at: datetime.datetime = Field(
        default_factory=lambda: datetime.datetime.now(datetime.timezone.utc)
    )


class TranscriptionHistoryItem(BaseModel):
    """A single item in the transcription history list.

    Attributes:
        id: Unique transcription identifier.
        filename: Original audio filename.
        title: Optional human-readable title.
        emoji: Optional emoji for the transcription.
        tags: List of categorisation tags.
        language: Language code.
        provider: Transcription provider name.
        duration_s: Duration of the source audio in seconds.
        created_at: UTC timestamp.
    """

    id: str
    filename: str
    title: str | None = None
    emoji: str | None = None
    tags: list[str] = Field(default_factory=list)
    language: str = "es"
    provider: str = "unknown"
    duration_s: float = 0.0
    created_at: datetime.datetime = Field(
        default_factory=lambda: datetime.datetime.now(datetime.timezone.utc)
    )
