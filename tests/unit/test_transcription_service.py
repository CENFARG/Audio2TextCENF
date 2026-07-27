"""@File: tests/unit/test_transcription_service.py
@Description: Unit tests for TranscriptionService orchestrator (Task 3.7). TDD cycle.
@Version: 0.16.0
@Author: CENF Development Team
@License: Apache-2.0
"""

from __future__ import annotations

from unittest.mock import MagicMock


class TestTranscriptionServiceInit:
    """Tests for TranscriptionService initialization."""

    def test_create_with_provider_and_pipeline(self) -> None:
        """Service can be constructed with provider, pipeline, and metadata service."""
        from audio2text.services.transcription_service import TranscriptionService

        mock_provider = MagicMock()
        mock_provider.provider_name = "mock"
        mock_provider.model_name = "mock-model"
        mock_provider.is_available = True

        mock_pipeline = MagicMock()

        mock_metadata = MagicMock()

        service = TranscriptionService(
            provider=mock_provider,
            pipeline=mock_pipeline,
            metadata_service=mock_metadata,
        )
        assert service is not None


class TestTranscriptionServiceTranscribe:
    """Tests for the transcribe() method."""

    def test_transcribe_invokes_provider(self) -> None:
        """transcribe() calls the provider and returns a TranscriptionResult."""
        from audio2text.domain.transcription import TranscriptionResult
        from audio2text.services.transcription_service import TranscriptionService

        mock_provider = MagicMock()
        mock_provider.provider_name = "mock"
        mock_provider.model_name = "mock-model"
        mock_provider.is_available = True
        mock_provider.transcribe_file.return_value = TranscriptionResult(
            text="Hola mundo",
            duration_seconds=2.0,
            language="es",
            provider_name="mock",
            model_name="mock-model",
        )

        mock_pipeline = MagicMock()
        from audio2text.pipeline.pipeline import PipelineResult

        mock_pipeline.process.return_value = PipelineResult(
            final_text="Hola mundo", stages_executed=0, stage_results=[]
        )

        mock_metadata = MagicMock()

        service = TranscriptionService(
            provider=mock_provider,
            pipeline=mock_pipeline,
            metadata_service=mock_metadata,
        )

        result = service.transcribe("test.wav")

        mock_provider.transcribe_file.assert_called_once_with("test.wav", language="es")
        assert result is not None
        assert result.text == "Hola mundo"

    def test_transcribe_with_language_override(self) -> None:
        """transcribe() passes language parameter to the provider."""
        from audio2text.domain.transcription import TranscriptionResult
        from audio2text.services.transcription_service import TranscriptionService

        mock_provider = MagicMock()
        mock_provider.provider_name = "mock"
        mock_provider.model_name = "mock-model"
        mock_provider.is_available = True
        mock_provider.transcribe_file.return_value = TranscriptionResult(
            text="Hello world", duration_seconds=1.0, language="en",
        )

        mock_pipeline = MagicMock()
        from audio2text.pipeline.pipeline import PipelineResult

        mock_pipeline.process.return_value = PipelineResult(
            final_text="Hello world", stages_executed=0, stage_results=[]
        )
        mock_metadata = MagicMock()

        service = TranscriptionService(
            provider=mock_provider,
            pipeline=mock_pipeline,
            metadata_service=mock_metadata,
        )

        result = service.transcribe("test.wav", language="en")
        mock_provider.transcribe_file.assert_called_once_with("test.wav", language="en")
        assert result.language == "en"

    def test_transcribe_passes_text_through_pipeline(self) -> None:
        """After transcription, text flows through the pipeline."""
        from audio2text.domain.transcription import TranscriptionResult
        from audio2text.services.transcription_service import TranscriptionService

        mock_provider = MagicMock()
        mock_provider.provider_name = "mock"
        mock_provider.model_name = "mock-model"
        mock_provider.is_available = True
        mock_provider.transcribe_file.return_value = TranscriptionResult(
            text="texto original", duration_seconds=1.0, language="es",
        )

        mock_pipeline = MagicMock()
        from audio2text.pipeline.pipeline import PipelineResult

        mock_pipeline.process.return_value = PipelineResult(
            final_text="texto procesado", stages_executed=2, stage_results=[]
        )
        mock_metadata = MagicMock()

        service = TranscriptionService(
            provider=mock_provider,
            pipeline=mock_pipeline,
            metadata_service=mock_metadata,
        )

        result = service.transcribe("test.wav")
        # Pipeline.process was called with the provider's text
        mock_pipeline.process.assert_called_once_with("texto original")
        assert result.text == "texto procesado"

    def test_transcribe_provider_failure_returns_none(self) -> None:
        """When the provider fails, transcribe() returns None."""
        from audio2text.services.transcription_service import TranscriptionService

        mock_provider = MagicMock()
        mock_provider.provider_name = "mock"
        mock_provider.transcribe_file.return_value = None
        mock_provider.is_available = True

        mock_pipeline = MagicMock()
        mock_metadata = MagicMock()

        service = TranscriptionService(
            provider=mock_provider,
            pipeline=mock_pipeline,
            metadata_service=mock_metadata,
        )

        result = service.transcribe("test.wav")
        assert result is None

    def test_transcribe_provider_unavailable_returns_none(self) -> None:
        """When provider is not available, transcribe() returns None."""
        from audio2text.services.transcription_service import TranscriptionService

        mock_provider = MagicMock()
        mock_provider.is_available = False

        mock_pipeline = MagicMock()
        mock_metadata = MagicMock()

        service = TranscriptionService(
            provider=mock_provider,
            pipeline=mock_pipeline,
            metadata_service=mock_metadata,
        )

        result = service.transcribe("test.wav")
        assert result is None
