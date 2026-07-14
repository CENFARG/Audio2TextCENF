"""@File: tests/unit/test_nvidia_provider.py
@Description: Unit tests for NvidiaRivaProvider (Task 2.5).
@Version: 0.16.0
@Author: CENF Development Team
@License: Apache-2.0
"""

from __future__ import annotations

import pytest


class TestNvidiaRivaProvider:
    """Tests for the NVIDIA Riva transcription provider (gRPC-based)."""

    def test_provider_name_is_nvidia(self) -> None:
        """NvidiaRivaProvider reports its name as 'nvidia'."""
        from audio2text.providers.nvidia_riva_provider import NvidiaRivaProvider

        provider = NvidiaRivaProvider({})
        assert provider.provider_name == "nvidia"

    def test_model_name_default_is_parakeet(self) -> None:
        """Default model is 'parakeet-1.1b'."""
        from audio2text.providers.nvidia_riva_provider import NvidiaRivaProvider

        provider = NvidiaRivaProvider({})
        assert provider.model_name == "parakeet-1.1b"

    def test_model_name_configurable(self) -> None:
        """Model name can be overridden via config."""
        from audio2text.providers.nvidia_riva_provider import NvidiaRivaProvider

        provider = NvidiaRivaProvider({"model": "parakeet-ctc-0.6b-es"})
        assert provider.model_name == "parakeet-ctc-0.6b-es"

    def test_is_available_false_without_deps_or_service(self) -> None:
        """Without riva-client or a running server, is_available is False."""
        from audio2text.providers.nvidia_riva_provider import NvidiaRivaProvider

        provider = NvidiaRivaProvider({})
        # In test env without NVIDIA API key or running Riva server → unavailable
        assert provider.is_available is False

    def test_transcribe_file_returns_none_when_unavailable(self) -> None:
        """transcribe_file returns None when provider is not available."""
        from audio2text.providers.nvidia_riva_provider import NvidiaRivaProvider

        provider = NvidiaRivaProvider({})
        result = provider.transcribe_file("test.wav")
        assert result is None

    def test_transcribe_stream_raises_not_implemented(self) -> None:
        """transcribe_stream raises NotImplementedError."""
        from audio2text.providers.nvidia_riva_provider import NvidiaRivaProvider

        provider = NvidiaRivaProvider({})
        with pytest.raises(NotImplementedError, match="streaming"):
            provider.transcribe_stream(None)

    def test_validate_config_reports_issues_when_unavailable(self) -> None:
        """validate_config reports issues when client is not available."""
        from audio2text.providers.nvidia_riva_provider import NvidiaRivaProvider

        provider = NvidiaRivaProvider({})
        issues = provider.validate_config()
        assert isinstance(issues, list)
        assert len(issues) >= 1

    def test_cloud_mode_uses_ssl(self) -> None:
        """Cloud mode uses SSL by default."""
        from audio2text.providers.nvidia_riva_provider import NvidiaRivaProvider

        provider = NvidiaRivaProvider({"mode": "cloud"})
        assert provider._mode == "cloud"
        assert provider._use_ssl is True

    def test_local_mode_no_ssl(self) -> None:
        """Local mode disables SSL by default."""
        from audio2text.providers.nvidia_riva_provider import NvidiaRivaProvider

        provider = NvidiaRivaProvider({"mode": "local", "use_ssl": False})
        assert provider._mode == "local"
        assert provider._use_ssl is False

    def test_configurable_host_and_port(self) -> None:
        """Host and port can be configured."""
        from audio2text.providers.nvidia_riva_provider import NvidiaRivaProvider

        provider = NvidiaRivaProvider(
            {"host": "my-riva-server.local", "port": 50051, "use_ssl": False}
        )
        assert provider._host == "my-riva-server.local"
        assert provider._port == 50051

    def test_accepts_language_parameter(self) -> None:
        """transcribe_file accepts language parameter."""
        from audio2text.providers.nvidia_riva_provider import NvidiaRivaProvider

        provider = NvidiaRivaProvider({})
        result = provider.transcribe_file("test.wav", language="en")
        assert result is None  # Not available, doesn't crash
