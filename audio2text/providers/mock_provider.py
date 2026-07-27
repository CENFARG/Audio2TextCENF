"""@File: audio2text/providers/mock_provider.py
@Description: Mock transcription provider for testing and development.
@Version: 0.16.0
@Author: CENF Development Team
@License: Apache-2.0
"""

from __future__ import annotations

from typing import Any

from audio2text.domain.transcription import TranscriptionResult
from audio2text.providers.base import TranscriptionProvider


class MockProvider(TranscriptionProvider):
    """A mock transcription provider that returns pre-configured results.

    Always available. Useful for integration tests, CI pipelines,
    and development when no real transcription service is accessible.
    """

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        """Initialize MockProvider with optional canned configuration.

        Args:
            config: Dictionary that may contain:
                - text: Canned transcription text (default "Mock transcription result")
                - language: Language code (default "es")
                - confidence: Confidence score (default 0.99)
                - error_after: Number of calls before raising (None = never)
                - delay_ms: Simulated processing delay (default 0)
        """
        cfg = config or {}
        self._text: str = cfg.get("text", "Mock transcription result")
        self._language: str = cfg.get("language", "es")
        self._confidence: float = cfg.get("confidence", 0.99)
        self._error_after: int | None = cfg.get("error_after")
        self._delay_ms: int = cfg.get("delay_ms", 0)
        self._call_count: int = 0

    # ------------------------------------------------------------------
    # TranscriptionProvider interface
    # ------------------------------------------------------------------

    def transcribe_file(
        self, audio_path: str, language: str | None = None
    ) -> TranscriptionResult | None:
        """Return a canned transcription result.

        If error_after is configured and the call count exceeds it,
        simulates a failure by returning None.
        """
        self._call_count += 1

        if self._error_after is not None and self._call_count > self._error_after:
            return None

        if self._delay_ms > 0:
            import time

            time.sleep(self._delay_ms / 1000.0)

        return TranscriptionResult(
            text=self._text,
            duration_seconds=1.0,
            language=language if language is not None else self._language,
            confidence=self._confidence,
            provider_name=self.provider_name,
            model_name=self.model_name,
        )

    def transcribe_stream(
        self, audio_stream: Any, language: str = "es"
    ) -> TranscriptionResult | None:
        """Return a canned result for stream transcription."""
        return self.transcribe_file("stream", language)

    @property
    def is_available(self) -> bool:
        """MockProvider is always available."""
        return True

    @property
    def provider_name(self) -> str:
        return "mock"

    @property
    def model_name(self) -> str:
        return "mock-model"

    def validate_config(self) -> list[str]:
        """Mock configuration is always valid."""
        return []
