"""@File: audio2text/providers/faster_whisper_provider.py
@Description: faster-whisper transcription provider — local, optimized Whisper.
@Version: 0.16.0
@Author: CENF Development Team
@License: Apache-2.0
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from audio2text.domain.transcription import TranscriptionResult
from audio2text.providers.base import TranscriptionProvider


class FasterWhisperProvider(TranscriptionProvider):
    """Transcription provider using faster-whisper (CTranslate2-optimized Whisper).

    Runs entirely locally — no API key or internet required.
    Uses lazy model loading: the model is only loaded on first transcription request.
    Auto-detects CUDA GPU if available.

    Attributes:
        _config: Provider-specific configuration.
        _model_size: Whisper model size (tiny/base/small/medium/large-v3).
        _device: Compute device (auto/cpu/cuda).
        _model: The WhisperModel instance (lazy-loaded).
    """

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        """Initialize FasterWhisperProvider.

        Args:
            config: Configuration dict with optional keys:
                - model_size: Model size (default "base").
                - device: Device preference (default "auto").
                - compute_type: CTranslate2 compute type (default "auto").
                - models_dir: Directory for model storage.
                - vad_filter: Enable VAD (default True).
                - beam_size: Beam search width (default 5).
        """
        cfg = config or {}
        self._model_size: str = cfg.get("model_size", "base")
        self._device: str = cfg.get("device", "auto")
        self._compute_type: str = cfg.get("compute_type", "auto")
        self._models_dir: Path = Path(cfg.get("models_dir", "./models"))
        self._vad_filter: bool = cfg.get("vad_filter", True)
        self._beam_size: int = int(cfg.get("beam_size", 5))
        self._model: Any = None
        self._is_available: bool = True  # Set to False only if import fails

    def _load_model(self) -> bool:
        """Lazy-load the WhisperModel on first use.

        Returns:
            True if model loaded successfully, False otherwise.
        """
        if self._model is not None:
            return True

        try:
            from faster_whisper import WhisperModel

            # Resolve device
            device = self._device
            if device == "auto":
                import torch

                device = "cuda" if torch.cuda.is_available() else "cpu"

            # Resolve compute type
            compute_type = self._compute_type
            if compute_type == "auto":
                compute_type = "float16" if device == "cuda" else "int8"

            self._model = WhisperModel(
                self._model_size,
                device=device,
                compute_type=compute_type,
                download_root=str(self._models_dir),
            )
            return True
        except ImportError:
            self._is_available = False
            return False
        except Exception:
            self._is_available = False
            return False

    # ------------------------------------------------------------------
    # TranscriptionProvider interface
    # ------------------------------------------------------------------

    def transcribe_file(
        self, audio_path: str, language: str = "es"
    ) -> TranscriptionResult | None:
        """Transcribe an audio file using faster-whisper.

        Args:
            audio_path: Path to the audio file.
            language: Language code (default "es").

        Returns:
            TranscriptionResult or None on failure.
        """
        if not self._load_model():
            return None

        if not os.path.exists(audio_path):
            return None

        try:
            segments, info = self._model.transcribe(
                audio_path,
                language=language,
                beam_size=self._beam_size,
                vad_filter=self._vad_filter,
                word_timestamps=False,
            )

            transcript_parts: list[str] = []
            for segment in segments:
                if segment.text:
                    transcript_parts.append(segment.text.strip())

            full_text = " ".join(transcript_parts).strip()

            if not full_text:
                return None

            return TranscriptionResult(
                text=full_text,
                duration_seconds=info.duration,
                language=language,
                provider_name=self.provider_name,
                model_name=self.model_name,
            )
        except Exception:
            return None

    def transcribe_stream(
        self, audio_stream: Any, language: str = "es"
    ) -> TranscriptionResult | None:
        """Streaming transcription not yet implemented for FasterWhisper."""
        raise NotImplementedError(
            "faster-whisper streaming transcription not yet implemented"
        )

    @property
    def is_available(self) -> bool:
        return self._is_available

    @property
    def provider_name(self) -> str:
        return "faster_whisper"

    @property
    def model_name(self) -> str:
        return self._model_size

    def validate_config(self) -> list[str]:
        """Validate faster-whisper configuration.

        Checks that the model can be loaded.
        """
        issues: list[str] = []
        if not self._load_model():
            issues.append(
                f"faster-whisper model '{self._model_size}' could not be loaded. "
                "Ensure faster-whisper is installed and the model is downloaded."
            )
        return issues
