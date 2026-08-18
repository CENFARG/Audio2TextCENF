"""Tests for audio2text.config — comprehensive config schema and migration tests."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from audio2text.config.schema import (
    Audio2TextConfig,
    AudioConfig,
    ProvidersConfig,
    GroqProviderConfig,
    HotkeyConfig,
    LocalizationConfig,
    UiConfig,
)
from audio2text.config.migration import ConfigMigrator
from audio2text.config._decoder import decode_xor_key


class TestAudio2TextConfig:
    """Tests for the root config schema."""

    def test_default_creation(self):
        """Should create with all defaults."""
        config = Audio2TextConfig()
        assert config.version == "0.16.0"
        assert config.providers.primary == "groq"
        assert config.audio.sample_rate_hz == 16000
        assert config.audio.output_language == "es"

    def test_nested_access(self):
        """Should access nested config fields."""
        config = Audio2TextConfig()
        assert config.providers.groq.model == "whisper-large-v3"
        assert config.hotkey.record_toggle == "f8"
        assert config.localization.language == "es_ES"

    def test_from_dict(self):
        """Should create from dictionary."""
        data = {
            "version": "0.16.0",
            "providers": {"primary": "groq"},
            "audio": {"output_language": "en"},
        }
        config = Audio2TextConfig(**data)
        assert config.audio.output_language == "en"

    def test_output_language_independent(self):
        """output_language should be independent of UI language."""
        config = Audio2TextConfig(
            audio=AudioConfig(output_language="en"),
            localization=LocalizationConfig(language="es_ES"),
        )
        assert config.audio.output_language == "en"
        assert config.localization.language == "es_ES"


class TestAudioConfig:
    """Tests for AudioConfig."""

    def test_defaults(self):
        """Should have sensible defaults."""
        config = AudioConfig()
        assert config.sample_rate_hz == 16000
        assert config.channels == 1
        assert config.save_recordings is True
        assert config.output_language == "es"

    def test_custom_output_language(self):
        """Should accept custom output language."""
        config = AudioConfig(output_language="en")
        assert config.output_language == "en"


class TestProvidersConfig:
    """Tests for ProvidersConfig."""

    def test_default_primary(self):
        """Default primary should be groq."""
        config = ProvidersConfig()
        assert config.primary == "groq"

    def test_groq_defaults(self):
        """Groq config should have sensible defaults."""
        config = ProvidersConfig()
        assert config.groq.model == "whisper-large-v3"
        assert config.groq.timeout_s == 60.0


class TestHotkeyConfig:
    """Tests for HotkeyConfig."""

    def test_defaults(self):
        """Should have sensible defaults."""
        config = HotkeyConfig()
        assert config.record_toggle == "f8"
        assert config.cancel == "Esc"
        assert config.enabled is True


class TestLocalizationConfig:
    """Tests for LocalizationConfig."""

    def test_defaults(self):
        """Should have sensible defaults."""
        config = LocalizationConfig()
        assert config.language == "es_ES"
        assert config.fallback == "en_US"


class TestUiConfig:
    """Tests for UiConfig."""

    def test_defaults(self):
        """Should have sensible defaults."""
        config = UiConfig()
        assert config.theme == "system"
        assert config.window_width == 1100
        assert config.auto_paste is True


class TestXorDecoder:
    """Tests for XOR key decoder."""

    def test_decode_groq_key(self):
        """Should decode XOR-obfuscated Groq key."""
        # Encode a test key
        test_key = "gsk_test123456789"
        xor_key = "CENF_SECRET"
        encoded = "".join(
            chr(ord(c) ^ ord(xor_key[i % len(xor_key)]))
            for i, c in enumerate(test_key)
        )
        import base64
        encoded_b64 = base64.b64encode(encoded.encode("latin-1")).decode()

        decoded = decode_xor_key(encoded_b64)
        assert decoded == test_key

    def test_plaintext_passthrough(self):
        """Should pass through plaintext keys."""
        assert decode_xor_key("gsk_abc123") == "gsk_abc123"
        assert decode_xor_key("sk-test") == "sk-test"
        assert decode_xor_key("nvapi-key") == "nvapi-key"

    def test_empty_returns_empty(self):
        """Empty string should return empty."""
        assert decode_xor_key("") == ""

    def test_invalid_returns_original(self):
        """Invalid base64 should return original."""
        assert decode_xor_key("not-valid-base64!!!") == "not-valid-base64!!!"


class TestConfigMigration:
    """Tests for ConfigMigrator."""

    def test_detect_old_config(self):
        """Should detect old config with groq_api_key at root."""
        migrator = ConfigMigrator()
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({"groq_api_key": "encoded", "hotkey": "f9"}, f)
            f.flush()
            result = migrator.detect_old_config(Path(f.name))
            assert result is True

    def test_detect_new_config(self):
        """Should detect new config with providers section."""
        migrator = ConfigMigrator()
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({"version": "0.16.0", "providers": {"primary": "groq"}}, f)
            f.flush()
            result = migrator.detect_old_config(Path(f.name))
            assert result is False

    def test_detect_nonexistent(self):
        """Non-existent file should return False."""
        migrator = ConfigMigrator()
        result = migrator.detect_old_config(Path("/nonexistent.json"))
        assert result is False

    def test_build_default_config(self):
        """Should build default config skeleton."""
        from audio2text.config._schema import build_default_config

        config = build_default_config()
        assert config["version"] == "0.16.0"
        assert "providers" in config
        assert "audio" in config
        assert "hotkey" in config


class TestDefaultsLoader:
    """Tests for defaults.yaml loader."""

    def test_load_defaults(self):
        """Should load defaults from YAML."""
        import yaml
        defaults_path = Path(__file__).parent.parent.parent / "audio2text" / "config" / "defaults.yaml"
        with open(defaults_path, "r", encoding="utf-8") as f:
            defaults = yaml.safe_load(f)
        assert defaults is not None
        assert "version" in defaults
        assert defaults["version"] == "0.16.0"

    def test_defaults_has_providers(self):
        """Defaults should include providers."""
        import yaml
        defaults_path = Path(__file__).parent.parent.parent / "audio2text" / "config" / "defaults.yaml"
        with open(defaults_path, "r", encoding="utf-8") as f:
            defaults = yaml.safe_load(f)
        assert "providers" in defaults
        assert defaults["providers"]["primary"] == "groq"

    def test_defaults_has_audio(self):
        """Defaults should include audio config."""
        import yaml
        defaults_path = Path(__file__).parent.parent.parent / "audio2text" / "config" / "defaults.yaml"
        with open(defaults_path, "r", encoding="utf-8") as f:
            defaults = yaml.safe_load(f)
        assert "audio" in defaults
        assert defaults["audio"]["output_language"] == "es"
