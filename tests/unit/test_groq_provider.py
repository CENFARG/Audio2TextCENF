"""@File: tests/unit/test_groq_provider.py
@Description: Unit tests for GroqProvider (Task 2.4).
@Version: 0.16.0
@Author: CENF Development Team
@License: Apache-2.0
"""

from __future__ import annotations

from typing import Any

import pytest


class TestGroqProvider:
    """Tests for the Groq Cloud Whisper transcription provider."""

    def test_provider_name_is_groq(self) -> None:
        """GroqProvider reports its name as 'groq'."""
        from audio2text.providers.groq_provider import GroqProvider

        provider = GroqProvider({})
        assert provider.provider_name == "groq"

    def test_model_name_default(self) -> None:
        """Default model name is 'whisper-large-v3'."""
        from audio2text.providers.groq_provider import GroqProvider

        provider = GroqProvider({})
        assert provider.model_name == "whisper-large-v3"

    def test_model_name_configurable(self) -> None:
        """Model name can be overridden via config."""
        from audio2text.providers.groq_provider import GroqProvider

        provider = GroqProvider({"model": "whisper-large-v3-turbo"})
        assert provider.model_name == "whisper-large-v3-turbo"

    def test_is_available_false_without_api_key(self) -> None:
        """Without a Groq API key in SecretManager, is_available is False."""
        from audio2text.providers.groq_provider import GroqProvider

        provider = GroqProvider({})
        # No API key set → client fails to initialize
        assert provider.is_available is False

    def test_transcribe_file_returns_none_when_unavailable(self) -> None:
        """transcribe_file returns None when provider is not available."""
        from audio2text.providers.groq_provider import GroqProvider

        provider = GroqProvider({})
        assert not provider.is_available
        result = provider.transcribe_file("nonexistent.wav")
        assert result is None

    def test_transcribe_stream_raises_not_implemented(self) -> None:
        """transcribe_stream raises NotImplementedError (not yet supported)."""
        from audio2text.providers.groq_provider import GroqProvider

        provider = GroqProvider({})
        with pytest.raises(NotImplementedError, match="streaming"):
            provider.transcribe_stream(None)

    def test_validate_config_returns_missing_key_issue(self) -> None:
        """validate_config reports missing API key."""
        from audio2text.providers.groq_provider import GroqProvider

        provider = GroqProvider({})
        issues = provider.validate_config()
        assert isinstance(issues, list)
        assert len(issues) >= 1
        assert any("API key" in issue for issue in issues)

    def test_validate_config_detects_invalid_key_format(
        self, secret_manager: Any
    ) -> None:
        """validate_config reports invalid key format (must start with gsk_)."""
        from unittest.mock import patch

        from audio2text.providers.groq_provider import GroqProvider

        # Store an invalid-format key
        secret_manager.set("groq_api_key", "invalid_key_format")

        # Mock cenf_core.secrets.manager.SecretManager to return our test SM
        with patch(
            "cenf_core.secrets.manager.SecretManager",
            autospec=True,
        ) as mock_sm_cls:
            mock_sm_cls.return_value.get.side_effect = secret_manager.get

            provider = GroqProvider({})
            issues = provider.validate_config()
            assert any("gsk_" in issue for issue in issues)

    def test_validate_config_empty_when_api_key_valid(
        self, secret_manager: Any
    ) -> None:
        """validate_config returns empty list when API key is valid."""
        from unittest.mock import patch

        from audio2text.providers.groq_provider import GroqProvider

        # Store a valid-format key
        secret_manager.set("groq_api_key", "gsk_test_key_12345")

        with patch(
            "cenf_core.secrets.manager.SecretManager",
            autospec=True,
        ) as mock_sm_cls:
            mock_sm_cls.return_value.get.side_effect = secret_manager.get

            provider = GroqProvider({})
            issues = provider.validate_config()
            assert issues == []

    def test_applies_language_parameter(self) -> None:
        """transcribe_file accepts language parameter."""
        from audio2text.providers.groq_provider import GroqProvider

        provider = GroqProvider({})
        # Provider is unavailable, so returns None — but signature is correct
        result = provider.transcribe_file("test.wav", language="en")
        assert result is None  # Not available, so no transcription
