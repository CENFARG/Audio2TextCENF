"""@File: audio2text/services/transcription_service.py
@Description: TranscriptionService — orchestrates audio transcription end-to-end.
    Routes to the configured TranscriptionProvider, runs post-transcription pipeline,
    and returns the final TranscriptionResult.
@Version: 0.16.0
@Author: CENF Development Team
@License: Apache-2.0
"""

from __future__ import annotations

from audio2text.domain.transcription import TranscriptionResult
from audio2text.pipeline.pipeline import TranscriptionPipeline
from audio2text.providers.base import TranscriptionProvider
from audio2text.services.metadata_service import MetadataService


class TranscriptionService:
    """Orchestrates the full transcription workflow.

    Coordinates:
    1. Transcription via a configured ``TranscriptionProvider``.
    2. Post-transcription text processing via a ``TranscriptionPipeline``.
    3. Metadata persistence via ``MetadataService``.

    This is the main entry point for the services layer — it wires
    together all the individual services into one coherent workflow.
    """

    def __init__(
        self,
        provider: TranscriptionProvider,
        pipeline: TranscriptionPipeline,
        metadata_service: MetadataService,
    ) -> None:
        """Initialize the transcription service.

        Args:
            provider: A configured transcription provider (Groq, faster-whisper, etc.).
            pipeline: The post-transcription processing pipeline.
            metadata_service: Service for persisting transcription metadata.
        """
        self._provider = provider
        self._pipeline = pipeline
        self._metadata_service = metadata_service

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def transcribe(
        self, audio_path: str, language: str = "es"
    ) -> TranscriptionResult | None:
        """Transcribe an audio file and process the result.

        Workflow:
        1. Check provider availability.
        2. Call ``provider.transcribe_file(audio_path, language)``.
        3. If transcription succeeded, run the text through the pipeline.
        4. Return the final ``TranscriptionResult`` with processed text.

        Args:
            audio_path: Path to the audio file.
            language: Language code (default "es").

        Returns:
            A TranscriptionResult with processed text, or None if transcription failed.
        """
        if not self._provider.is_available:
            return None

        result = self._provider.transcribe_file(audio_path, language=language)
        if result is None:
            return None

        # Run post-transcription pipeline
        pipeline_result = self._pipeline.process(result.text)

        # Return result with pipeline-processed text
        return TranscriptionResult(
            text=pipeline_result.final_text,
            duration_seconds=result.duration_seconds,
            language=result.language,
            segments=result.segments,
            confidence=result.confidence,
            provider_name=result.provider_name,
            model_name=result.model_name,
        )
