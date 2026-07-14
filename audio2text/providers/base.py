"""@File: audio2text/providers/base.py
@Description: Abstract base class for all transcription providers (Strategy pattern).
@Version: 0.16.0
@Author: CENF Development Team
@License: Apache-2.0
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from audio2text.domain.transcription import TranscriptionResult


class TranscriptionProvider(ABC):
    """Abstract base class for transcription providers.

    All transcription backends (Groq, faster-whisper, NVIDIA Riva, Mock)
    must implement this interface. This enables the factory to create
    any provider and the service layer to use them polymorphically.

    Subclasses MUST implement:
        - transcribe_file
        - transcribe_stream
        - is_available (property)
        - provider_name (property)
        - model_name (property)
        - validate_config
    """

    @abstractmethod
    def transcribe_file(
        self, audio_path: str, language: str = "es"
    ) -> TranscriptionResult | None:
        """Transcribe an audio file and return the result.

        Args:
            audio_path: Path to the audio file (WAV, MP3, FLAC).
            language: Language code (default "es").

        Returns:
            A TranscriptionResult if successful, or None if transcription failed.
        """
        ...

    @abstractmethod
    def transcribe_stream(
        self, audio_stream: Any, language: str = "es"
    ) -> TranscriptionResult | None:
        """Transcribe from a live audio stream.

        Args:
            audio_stream: An audio stream object (implementation-specific).
            language: Language code (default "es").

        Returns:
            A TranscriptionResult if successful, or None.
        """
        ...

    @property
    @abstractmethod
    def is_available(self) -> bool:
        """Check if the provider is ready for transcription.

        Returns:
            True if the provider can transcribe (model loaded, API key valid, etc.).
        """
        ...

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Human-readable provider identifier (e.g., "groq", "faster_whisper").

        Returns:
            The provider type string.
        """
        ...

    @property
    @abstractmethod
    def model_name(self) -> str:
        """The model name currently in use.

        Returns:
            Model identifier string (e.g., "whisper-large-v3").
        """
        ...

    @abstractmethod
    def validate_config(self) -> list[str]:
        """Validate the provider configuration.

        Returns:
            A list of issue descriptions. Empty list means valid configuration.
        """
        ...
