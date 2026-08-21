"""@File: tests/unit/test_provider_fallback.py
@Description: Kaizen Nodal — Single Owner provider fallback contract.
    get_provider() must return an AVAILABLE provider always:
    - primary=groq without key -> falls back to mock (never unavailable)
    - primary=mock -> mock directly
@Version: 0.17.0
@Author: CENF Development Team
@License: Apache-2.0
"""

from __future__ import annotations

from unittest.mock import patch

import pytest


def _fake_config(get_string_result: str) -> object:
    """ConfigManager stub exposing get_string() only."""

    class _Cfg:
        def get_string(self, key: str, default: str | None = None) -> str | None:
            if key == "providers.primary":
                return get_string_result
            return default

    return _Cfg()


def test_get_provider_falls_back_to_mock_when_groq_unavailable() -> None:
    """No Groq key -> fallback MockProvider (always available)."""
    from audio2text.api.dependencies import get_provider

    cfg = _fake_config("groq")
    with patch("audio2text.api.dependencies.get_config", return_value=cfg):
        provider = get_provider()
    assert provider is not None
    assert provider.is_available is True
    # Fallback to mock when groq has no key
    assert provider.provider_name == "mock"


def test_get_provider_uses_mock_when_primary_is_mock() -> None:
    """primary=mock -> MockProvider directly."""
    from audio2text.api.dependencies import get_provider

    cfg = _fake_config("mock")
    with patch("audio2text.api.dependencies.get_config", return_value=cfg):
        provider = get_provider()
    assert provider is not None
    assert provider.is_available is True
    assert provider.provider_name == "mock"


def test_get_provider_with_valid_groq_key_uses_groq() -> None:
    """Groq key present -> GroqProvider (not mock)."""
    from audio2text.api.dependencies import get_provider

    cfg = _fake_config("groq")

    class _FakeGroq:
        is_available = True
        provider_name = "groq"

    with patch("audio2text.api.dependencies.get_config", return_value=cfg), patch(
        "audio2text.providers.factory.TranscriptionProviderFactory.create",
        return_value=_FakeGroq(),
    ):
        provider = get_provider()
    assert provider.provider_name == "groq"
    assert provider.is_available is True


def test_get_provider_never_returns_unavailable() -> None:
    """Invariant: get_provider() never returns an unavailable provider."""
    from audio2text.api.dependencies import get_provider

    for primary in ("groq", "faster_whisper", "nvidia", "mock"):
        cfg = _fake_config(primary)
        with patch("audio2text.api.dependencies.get_config", return_value=cfg):
            provider = get_provider()
        assert provider is not None, f"provider None for primary={primary}"
        assert provider.is_available is True, f"unavailable for primary={primary}"