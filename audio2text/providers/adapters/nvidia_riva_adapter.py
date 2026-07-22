"""@File: audio2text/providers/adapters/nvidia_riva_adapter.py
@Description: NVIDIA Riva transcription adapter — gRPC-based ASR (cloud or local).
@Version: 0.16.0
@Author: CENF Development Team
@License: Apache-2.0
"""

from __future__ import annotations

import os
from typing import Any

from audio2text.domain.transcription import TranscriptionResult


class NvidiaRivaProvider:
    """Transcription provider using NVIDIA Riva ASR via gRPC.

    Supports two modes:
        - Cloud: grpc.nvcf.nvidia.com:443 (requires NVIDIA API key)
        - Local: localhost:50051 (requires Docker NIM Riva container)

    Attributes:
        _mode: Operation mode ("cloud" or "local").
        _server: gRPC server address.
        _model: Model identifier.
        _is_available: Whether the gRPC client initialized successfully.
    """

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        """Initialize NvidiaRivaProvider.

        Args:
            config: Configuration dict with optional keys:
                - mode: "cloud" (default) or "local".
                - host: Server hostname.
                - port: Server port.
                - use_ssl: Enable TLS.
                - api_key_secret_key: SecretManager key for API key.
                - model: Model name (default "parakeet-1.1b").
        """
        cfg = config or {}
        self._mode: str = cfg.get("mode", "cloud")
        self._host: str = cfg.get("host", "grpc.nvcf.nvidia.com")
        self._port: int = int(cfg.get("port", 443))
        self._use_ssl: bool = cfg.get("use_ssl", True)
        self._api_key_secret_key: str = cfg.get("api_key_secret_key", "nvidia_api_key")
        self._model: str = cfg.get("model", "parakeet-1.1b")
        self._is_available: bool = False
        self._asr_service: Any = None
        self._init_client()

    def _init_client(self) -> None:
        """Initialize the NVIDIA Riva gRPC client."""
        try:
            import riva.client
            from core_infrastructure.secrets import InMemorySecretAdapter

            # Build metadata for authentication
            metadata: list[tuple[str, str]] = []

            if self._mode == "cloud":
                secret_mgr = InMemorySecretAdapter()
                import asyncio
                api_key = asyncio.run(secret_mgr.get_secret(self._api_key_secret_key))
                if api_key:
                    # function-id for parakeet models
                    function_id = "a9eeee8f-b509-4712-b19d-194361fa5f31"
                    metadata.append(("function-id", function_id))
                    metadata.append(("authorization", f"Bearer {api_key}"))

            server_uri = f"{self._host}:{self._port}"

            auth = riva.client.Auth(
                use_ssl=self._use_ssl,
                uri=server_uri,
                metadata_args=metadata,
            )

            self._asr_service = riva.client.ASRService(auth)
            self._is_available = True
        except ImportError:
            self._is_available = False
        except Exception:
            self._is_available = False

    # ------------------------------------------------------------------
    # TranscriptionProvider interface
    # ------------------------------------------------------------------

    def transcribe_file(
        self, audio_path: str, language: str = "es"
    ) -> TranscriptionResult | None:
        """Transcribe an audio file using NVIDIA Riva.

        Args:
            audio_path: Path to the audio file. Must be 16-bit mono WAV at 16kHz.
            language: Language code (default "es"; mapped to "es-US" for Riva).

        Returns:
            TranscriptionResult or None on failure.
        """
        if not self._is_available or not self._asr_service:
            return None

        if not os.path.exists(audio_path):
            return None

        try:
            import riva.client

            lang_code = "es-US" if language.startswith("es") else "en-US"

            config = riva.client.StreamingRecognitionConfig(
                config=riva.client.RecognitionConfig(
                    language_code=lang_code,
                    enable_automatic_punctuation=True,
                    verbatim_transcripts=False,
                ),
                interim_results=False,
            )

            responses = self._asr_service.streaming_response_generator(
                audio_chunks=riva.client.AudioChunkFileIterator(
                    audio_path,
                    1600,  # chunk_size in frames
                    None,  # no delay callback
                ),
                streaming_config=config,
            )

            transcript_parts: list[str] = []
            for response in responses:
                if not response.results:
                    continue
                for result in response.results:
                    if not result.alternatives:
                        continue
                    alternative = result.alternatives[0]
                    if alternative.transcript:
                        transcript_parts.append(alternative.transcript)

            full_text = " ".join(transcript_parts).strip()

            if not full_text:
                return None

            return TranscriptionResult(
                text=full_text,
                duration_seconds=0.0,  # Riva doesn't report duration
                language=language,
                provider_name=self.provider_name,
                model_name=self.model_name,
            )
        except Exception:
            return None

    def transcribe_stream(
        self, audio_stream: Any, language: str = "es"
    ) -> TranscriptionResult | None:
        """Streaming transcription not yet implemented for NvidiaRiva."""
        raise NotImplementedError(
            "NVIDIA Riva streaming transcription not yet implemented"
        )

    @property
    def is_available(self) -> bool:
        return self._is_available

    @property
    def provider_name(self) -> str:
        return "nvidia"

    @property
    def model_name(self) -> str:
        return self._model

    def validate_config(self) -> list[str]:
        """Validate NVIDIA Riva configuration.

        Checks connectivity to the gRPC server.
        """
        issues: list[str] = []
        if not self._is_available:
            issues.append(
                f"NVIDIA Riva client could not connect to {self._host}:{self._port}. "
                "Ensure the server is running or the API key is valid."
            )
        if self._mode == "cloud" and self._use_ssl and not self._is_available:
            issues.append(
                "TLS configuration may be invalid — check SSL certificates."
            )
        return issues
