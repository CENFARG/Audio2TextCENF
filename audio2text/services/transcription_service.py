"""@File: audio2text/services/transcription_service.py
@Description: TranscriptionService — orchestrates audio transcription end-to-end.
    Routes to the configured TranscriptionProvider, runs post-transcription pipeline,
    and returns the final TranscriptionResult. Includes client-side audio chunking
    for long audio to prevent Groq seam loss.
@Version: 0.16.0
@Author: CENF Development Team
@License: Apache-2.0
"""

from __future__ import annotations

import logging
import os
from typing import Callable, Optional

from audio2text.domain.transcription import TranscriptionResult
from audio2text.pipeline.pipeline import TranscriptionPipeline
from audio2text.providers.ports import TranscriptionProvider
from audio2text.services.metadata_service import MetadataService
from audio2text.services.audio_chunker import (
    CHUNK_THRESHOLD_S,
    split_audio_on_silence,
    transcribe_chunks,
)

logger = logging.getLogger(__name__)


class TranscriptionService:
    """Orchestrates the full transcription workflow.

    Coordinates:
    1. Transcription via a configured ``TranscriptionProvider``.
    2. Post-transcription text processing via a ``TranscriptionPipeline``.
    3. Metadata persistence via ``MetadataService``.
    4. Client-side audio chunking for long audio (>=28s) to prevent
       Groq seam loss where words get cut at server-side window boundaries.

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
        self,
        audio_path: str,
        language: str = "es",
        output_language: Optional[str] = None,
        operation_id: Optional[str] = None,
        event_callback: Optional[Callable[[dict], None]] = None,
    ) -> TranscriptionResult | None:
        """Transcribe an audio file and process the result.

        For audio >= 28s, automatically chunks on the client side by
        cutting at silences to prevent Groq seam loss. Each chunk is
        transcribed with context from the previous chunk for consistency.

        Workflow:
        1. Check provider availability.
        2. Check audio duration — if >= CHUNK_THRESHOLD_S, use chunked transcription.
        3. Call provider for each chunk (or whole file if short).
        4. If transcription succeeded, run the text through the pipeline.
        5. Persist metadata via MetadataService.
        6. Return the final ``TranscriptionResult`` with processed text.

        Args:
            audio_path: Path to the audio file.
            language: Source language code (default "es").
            output_language: Output language code (if different from source).
            operation_id: Optional operation tracking ID.
            event_callback: Optional callback for chunk progress events.

        Returns:
            A TranscriptionResult with processed text, or None if transcription failed.
        """
        if not self._provider.is_available:
            return None

        # Check if audio is long enough to need chunking
        duration = self._get_audio_duration(audio_path)
        if duration is not None and duration >= CHUNK_THRESHOLD_S:
            logger.info(
                "Long audio (%.1fs): chunking in windows <30s to prevent "
                "Groq seam loss.",
                duration,
            )
            return self._transcribe_chunked(
                audio_path,
                language=language,
                operation_id=operation_id,
                event_callback=event_callback,
            )

        # Short audio: transcribe directly
        result = self._provider.transcribe_file(audio_path, language=language)
        if result is None:
            return None

        return self._process_result(result, language=language)

    def _transcribe_chunked(
        self,
        audio_path: str,
        language: str = "es",
        operation_id: Optional[str] = None,
        event_callback: Optional[Callable[[dict], None]] = None,
    ) -> TranscriptionResult | None:
        """Transcribe long audio using client-side chunking.

        Loads the audio, splits on silences, transcribes each chunk with
        context from the previous, and joins the results.
        """
        try:
            import soundfile as sf
            import numpy as np

            audio, sr = sf.read(audio_path)
            if audio.ndim > 1:
                audio = audio.mean(axis=1)  # Convert to mono

            def api_call(chunk: np.ndarray, prompt: Optional[str] = None) -> str:
                """Transcribe a single chunk using the provider."""
                # Write chunk to temp file
                import tempfile

                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                    sf.write(f.name, chunk, sr)
                    chunk_path = f.name

                try:
                    result = self._provider.transcribe_file(
                        chunk_path, language=language
                    )
                    return result.text if result else ""
                finally:
                    if os.path.exists(chunk_path):
                        os.unlink(chunk_path)

            # Transcribe all chunks
            full_text = transcribe_chunks(
                audio,
                sr,
                api_call=api_call,
                operation_id=operation_id,
                event_callback=event_callback,
            )

            if not full_text:
                return None

            # Create result from joined text
            from audio2text.domain.transcription import TranscriptionResult

            result = TranscriptionResult(
                text=full_text,
                duration_seconds=self._get_audio_duration(audio_path) or 0.0,
                language=language,
                provider_name=self._provider.provider_name,
                model_name=self._provider.model_name,
            )

            return self._process_result(result, language=language)

        except Exception as e:
            logger.error("Chunked transcription failed: %s", e)
            return None

    def _process_result(
        self,
        result: TranscriptionResult,
        language: str = "es",
    ) -> TranscriptionResult:
        """Process a transcription result through the pipeline and metadata service."""
        # Run post-transcription pipeline
        pipeline_result = self._pipeline.process(result.text)

        # Persist metadata
        try:
            self._metadata_service.record(
                text=pipeline_result.final_text,
                provider=result.provider_name,
                model=result.model_name,
                language=language,
                duration=result.duration_seconds,
            )
        except Exception as e:
            logger.warning("Failed to persist metadata: %s", e)

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

    def _get_audio_duration(self, audio_path: str) -> float | None:
        """Get audio file duration in seconds, returning None on failure."""
        try:
            import soundfile as sf

            info = sf.info(audio_path)
            return info.duration
        except Exception:
            return None
