"""
TranscriptionProvider Protocol — the contract every transcription adapter must satisfy.

Replaces the old ABC-based base.py with a structural Protocol.
Uses @runtime_checkable for isinstance checks in tests.
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from audio2text.domain.transcription import TranscriptionResult


@runtime_checkable
class TranscriptionProvider(Protocol):
    """Structural contract for transcription backends.

    All adapters (Groq, faster-whisper, NVIDIA Riva, Mock) satisfy this
    Protocol through duck-typing — no inheritance required.

    Methods:
        transcribe_file: Transcribe an audio file path.
        transcribe_stream: Transcribe from a live audio stream.
        is_available (property): Whether the provider is ready.
        provider_name (property): Human-readable provider identifier.
        model_name (property): Model identifier in use.
        validate_config: Validate provider configuration.
    """

    def transcribe_file(
        self, audio_path: str, language: str = "es"
    ) -> TranscriptionResult | None: ...

    def transcribe_stream(
        self, audio_stream: Any, language: str = "es"
    ) -> TranscriptionResult | None: ...

    @property
    def is_available(self) -> bool: ...

    @property
    def provider_name(self) -> str: ...

    @property
    def model_name(self) -> str: ...

    def validate_config(self) -> list[str]: ...