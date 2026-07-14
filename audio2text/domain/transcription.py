"""@File: audio2text/domain/transcription.py
@Description: Core transcription domain models — TranscriptionResult and TranscriptionConfig.
@Version: 0.16.0
@Author: CENF Development Team
@License: Apache-2.0
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class TranscriptionResult:
    """The output of a transcription operation.

    Attributes:
        text: The transcribed text.
        duration_seconds: Duration of the source audio in seconds.
        language: Language code (e.g., "es", "en").
        segments: Optional list of timestamped segments.
        confidence: Overall confidence score (0.0–1.0) if available.
        provider_name: Name of the transcription provider used.
        model_name: Name of the model used for transcription.
    """

    text: str
    duration_seconds: float
    language: str
    segments: list[dict[str, Any]] = field(default_factory=list)
    confidence: float | None = None
    provider_name: str | None = None
    model_name: str | None = None


@dataclass
class TranscriptionConfig:
    """Configuration for a transcription request.

    Attributes:
        provider_type: Identifier of the provider to use (e.g., "groq").
        language: Target language code (default "es").
        model: Specific model name override (optional).
        device: Device preference — "auto", "cpu", or "cuda" (default "auto").
        options: Additional provider-specific options as key-value pairs.
    """

    provider_type: str = "groq"
    language: str = "es"
    model: str | None = None
    device: str = "auto"
    options: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Ensure options dict is independent of the caller's reference."""
        self.options = dict(self.options)
