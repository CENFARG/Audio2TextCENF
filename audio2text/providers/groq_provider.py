"""@File: audio2text/providers/groq_provider.py
@Description: Groq transcription provider — wraps Groq Cloud Whisper API.
@Version: 0.16.0
@Author: CENF Development Team
@License: Apache-2.0
"""

from __future__ import annotations

from typing import Any

from audio2text.domain.transcription import TranscriptionResult
from audio2text.providers.base import TranscriptionProvider


class GroqProvider(TranscriptionProvider):
    """Transcription provider using Groq Cloud Whisper API.

    Wraps the `groq` Python SDK. Requires a valid Groq API key
    (stored via SecretManager under key "groq_api_key").

    Attributes:
        _config: Provider-specific configuration.
        _model: Model name (default "whisper-large-v3").
        _is_available: Whether the Groq client initialized successfully.
    """

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        """Initialize GroqProvider.

        Args:
            config: Configuration dict with optional keys:
                - api_key_secret_key: SecretManager key for the API key.
                - model: Model name (default "whisper-large-v3").
                - base_url: API base URL.
                - timeout_s: Request timeout in seconds.
                - max_retries: Max retries on rate limit.
        """
        cfg = config or {}
        self._api_key_secret_key: str = cfg.get("api_key_secret_key", "groq_api_key")
        self._model: str = cfg.get("model", "whisper-large-v3")
        self._base_url: str = cfg.get("base_url", "https://api.groq.com")
        self._timeout_s: float = float(cfg.get("timeout_s", 60.0))
        self._max_retries: int = int(cfg.get("max_retries", 3))
        self._is_available: bool = False
        self._client: Any = None
        self._init_client()

    def _init_client(self) -> None:
        """Initialize the Groq SDK client."""
        try:
            import groq as groq_sdk
            from cenf_core.secrets.manager import SecretManager

            secret_mgr = SecretManager()
            api_key = secret_mgr.get(self._api_key_secret_key)

            if not api_key:
                self._is_available = False
                return

            self._client = groq_sdk.Client(api_key=api_key, base_url=self._base_url)
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
        """Transcribe an audio file using Groq Whisper API.

        Args:
            audio_path: Path to the audio file.
            language: Language code (default "es").

        Returns:
            TranscriptionResult or None on failure.
        """
        if not self._is_available or not self._client:
            return None

        try:
            import os

            with open(audio_path, "rb") as audio_file:
                response = self._client.audio.transcriptions.create(
                    file=(os.path.basename(audio_path), audio_file.read()),
                    model=self._model,
                    response_format="text",
                    language=language,
                )

            return TranscriptionResult(
                text=response,
                duration_seconds=0.0,  # Groq text response doesn't include duration
                language=language,
                provider_name=self.provider_name,
                model_name=self.model_name,
            )
        except Exception:
            return None

    def transcribe_stream(
        self, audio_stream: Any, language: str = "es"
    ) -> TranscriptionResult | None:
        """Streaming transcription not yet implemented for GroqProvider."""
        raise NotImplementedError("Groq streaming transcription not yet implemented")

    @property
    def is_available(self) -> bool:
        return self._is_available

    @property
    def provider_name(self) -> str:
        return "groq"

    @property
    def model_name(self) -> str:
        return self._model

    def validate_config(self) -> list[str]:
        """Validate Groq configuration.

        Returns:
            List of issues. Checks that API key exists and is valid format.
        """
        issues: list[str] = []

        from cenf_core.secrets.manager import SecretManager

        secret_mgr = SecretManager()
        api_key = secret_mgr.get(self._api_key_secret_key)

        if not api_key:
            issues.append(
                f"Groq API key not found (key: {self._api_key_secret_key}). "
                "Set it via SecretManager or env var."
            )
        elif not api_key.startswith("gsk_"):
            issues.append(
                "Groq API key format is invalid — must start with 'gsk_'."
            )

        return issues
