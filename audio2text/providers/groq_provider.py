"""@File: audio2text/providers/groq_provider.py
@Description: Groq transcription provider — wraps Groq Cloud Whisper API.
@Version: 0.17.0
@Author: CENF Development Team
@License: Apache-2.0
"""

from __future__ import annotations

import logging
from typing import Any

from audio2text.domain.transcription import TranscriptionResult
from audio2text.providers.base import TranscriptionProvider

logger = logging.getLogger(__name__)

_singleton_secret_adapter = None


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

    @staticmethod
    def _get_api_key(key_name: str) -> str | None:
        """Retrieve API key from SecretManager via registry (Single Owner)."""
        try:
            from audio2text.infrastructure import get_registry
            import asyncio

            try:
                secrets = get_registry().get_secrets()
                try:
                    loop = asyncio.get_running_loop()
                except RuntimeError:
                    loop = None
                if loop and loop.is_running():
                    import concurrent.futures

                    def _run_in_thread() -> str | None:
                        return asyncio.run(secrets.get_secret(key_name))

                    with concurrent.futures.ThreadPoolExecutor() as pool:
                        fut = pool.submit(_run_in_thread)
                        try:
                            return fut.result(timeout=2)
                        except Exception:
                            return None
                else:
                    return asyncio.run(secrets.get_secret(key_name))
            except Exception:
                pass
        except Exception:
            pass
        # Fallback singleton
        try:
            from core_infrastructure.secrets import InMemorySecretAdapter  # type: ignore
            import asyncio

            global _singleton_secret_adapter
            if _singleton_secret_adapter is None:
                _singleton_secret_adapter = InMemorySecretAdapter()
            mgr = _singleton_secret_adapter
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = None
            if loop and loop.is_running():
                import concurrent.futures

                def _run_fallback() -> str | None:
                    return asyncio.run(mgr.get_secret(key_name))  # type: ignore

                with concurrent.futures.ThreadPoolExecutor() as pool:
                    fut = pool.submit(_run_fallback)
                    try:
                        return fut.result(timeout=2)
                    except Exception:
                        return None
            else:
                return asyncio.run(mgr.get_secret(key_name))  # type: ignore
        except Exception:
            return None
        # Legacy cenf_core fallback
        try:
            from cenf_core.secrets.manager import SecretManager  # type: ignore

            sm = SecretManager()
            return sm.get(key_name)
        except Exception:
            return None

    def _init_client(self) -> None:
        """Initialize the Groq SDK client."""
        try:
            import groq as groq_sdk

            api_key = self._get_api_key(self._api_key_secret_key)

            if not api_key:
                logger.warning("Groq API key not found (key: %s) — Groq no configurado — pega gsk_... para activar", self._api_key_secret_key)
                self._is_available = False
                return

            self._client = groq_sdk.Client(api_key=api_key, base_url=self._base_url)
            self._is_available = True
        except ImportError:
            logger.warning("groq SDK not installed — Groq provider unavailable")
            self._is_available = False
        except Exception as exc:
            logger.warning("Failed to init Groq client: %s", exc)
            self._is_available = False

    # ------------------------------------------------------------------
    # TranscriptionProvider interface
    # ------------------------------------------------------------------

    def transcribe_file(
        self, audio_path: str, language: str = "es"
    ) -> TranscriptionResult | None:
        """Transcribe an audio file using Groq Whisper API."""
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
                duration_seconds=0.0,
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
        """Validate Groq configuration."""
        issues: list[str] = []
        api_key: str | None = self._get_api_key(self._api_key_secret_key)
        # Also try legacy SecretManager if still none
        if api_key is None:
            try:
                from cenf_core.secrets.manager import SecretManager

                sm = SecretManager()
                api_key = sm.get(self._api_key_secret_key)
            except Exception:
                pass
        if not api_key:
            issues.append(
                f"Groq API key not found (key: {self._api_key_secret_key}). "
                "Set it via SecretManager or env var."
            )
        elif not api_key.startswith("gsk_"):
            issues.append("Groq API key format is invalid — must start with 'gsk_'.")
        return issues
