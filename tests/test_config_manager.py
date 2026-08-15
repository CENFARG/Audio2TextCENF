"""
Unit tests for ConfigManager class.

This module tests configuration management including:
- Loading and saving configuration
- API key obfuscation/deobfuscation
- Getting and setting configuration values
- Localization support
- Default configuration handling

Author: Audio2Text Development Team
Version: 0.13.0
"""

import pytest
import sys
import os
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.config_manager import ConfigManager


@pytest.mark.unit
class TestConfigManagerInitialization:
    """Tests for ConfigManager initialization."""

    def test_initialization_with_default_config(self):
        """Test initialization creates default configuration."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            config_file = f.name

        try:
            manager = ConfigManager(config_file=config_file)

            assert manager.config_file == config_file
            assert manager.config is not None
            assert "app_version" in manager.config
            assert manager.config["app_version"] == "0.15.0"
            assert manager.config["hotkey"] == "f12"
            assert manager.config["default_language"] == "es"
        finally:
            if os.path.exists(config_file):
                os.unlink(config_file)

    def test_initialization_loads_existing_config(self):
        """Test initialization loads existing configuration file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            config_file = f.name
            test_config = {"app_version": "0.12.0", "hotkey": "F10", "default_language": "en"}
            json.dump(test_config, f)

        try:
            manager = ConfigManager(config_file=config_file)

            # Should override with default version but keep other settings
            assert manager.config["app_version"] == "0.15.0"
            assert manager.config["hotkey"] == "F10"
            assert manager.config["default_language"] == "en"
        finally:
            if os.path.exists(config_file):
                os.unlink(config_file)


@pytest.mark.unit
class TestConfigManagerLoadSave:
    """Tests for loading and saving configuration."""

    @pytest.fixture
    def temp_config_file(self):
        """Create a temporary config file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            config_file = f.name
        yield config_file
        if os.path.exists(config_file):
            os.unlink(config_file)

    def test_load_config_creates_default(self, temp_config_file):
        """Test loading config when file doesn't exist creates default."""
        manager = ConfigManager(config_file=temp_config_file)

        assert manager.config is not None
        assert "hotkey" in manager.config
        assert "default_language" in manager.config

    def test_save_config(self, temp_config_file):
        """Test saving configuration to file."""
        manager = ConfigManager(config_file=temp_config_file)
        manager.config["hotkey"] = "F9"
        manager.save_config()

        # Load and verify
        with open(temp_config_file, "r", encoding="utf-8") as f:
            saved_config = json.load(f)

        # Key should be obfuscated
        assert saved_config["hotkey"] == "F9"
        assert "groq_api_key" in saved_config

    def test_save_config_obfuscates_keys(self, temp_config_file):
        """Test that API keys are obfuscated when saved."""
        manager = ConfigManager(config_file=temp_config_file)
        manager.config["groq_api_key"] = "gsk_test_key_12345"
        manager.save_config()

        with open(temp_config_file, "r", encoding="utf-8") as f:
            saved_config = json.load(f)

        # Should NOT be plain text
        assert not saved_config["groq_api_key"].startswith("gsk_")


@pytest.mark.unit
class TestConfigManagerGetSet:
    """Tests for getting and setting configuration values."""

    @pytest.fixture
    def manager(self):
        """Create a ConfigManager instance."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            config_file = f.name

        manager = ConfigManager(config_file=config_file)
        yield manager

        if os.path.exists(config_file):
            os.unlink(config_file)

    def test_get_existing_key(self, manager):
        """Test getting an existing configuration value."""
        hotkey = manager.get("hotkey")
        assert hotkey is not None
        assert isinstance(hotkey, str)

    def test_get_nonexistent_key_with_default(self, manager):
        """Test getting a non-existent key with default value."""
        value = manager.get("nonexistent_key", "default_value")
        assert value == "default_value"

    def test_get_nonexistent_key_no_default(self, manager):
        """Test getting a non-existent key without default."""
        value = manager.get("nonexistent_key")
        assert value is None

    def test_set_single_value(self, manager):
        """Test setting a single configuration value."""
        manager.set("hotkey", "F11")
        assert manager.get("hotkey") == "F11"

    def test_set_multiple_values(self, manager):
        """Test setting multiple configuration values."""
        new_settings = {"hotkey": "F7", "default_language": "en", "max_audio_files": 50}
        manager.set_multiple(new_settings)

        assert manager.get("hotkey") == "F7"
        assert manager.get("default_language") == "en"
        assert manager.get("max_audio_files") == 50


@pytest.mark.unit
class TestAPIKeyObfuscation:
    """Tests for API key obfuscation and deobfuscation."""

    @pytest.fixture
    def manager(self):
        """Create a ConfigManager instance."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            config_file = f.name

        manager = ConfigManager(config_file=config_file)
        yield manager

        if os.path.exists(config_file):
            os.unlink(config_file)

    def test_encode_key(self, manager):
        """Test encoding (obfuscating) an API key."""
        plain_key = "gsk_test_key_123456789"
        encoded = manager._encode_key(plain_key)

        assert encoded != plain_key
        assert isinstance(encoded, str)
        assert len(encoded) > 0

    def test_decode_key(self, manager):
        """Test decoding (deobfuscating) an API key."""
        plain_key = "gsk_test_key_123456789"
        encoded = manager._encode_key(plain_key)
        decoded = manager._decode_gift_key(encoded)

        assert decoded == plain_key

    def test_encode_decode_roundtrip(self, manager):
        """Test that encoding and decoding preserves the original key."""
        original_key = "gsk_abc123def456"
        encoded = manager._encode_key(original_key)
        decoded = manager._decode_gift_key(encoded)

        assert decoded == original_key

    def test_decode_invalid_encoded_key(self, manager):
        """Test decoding an invalid encoded key returns the input."""
        invalid_encoded = "not_a_valid_encoded_key"
        decoded = manager._decode_gift_key(invalid_encoded)

        # Should return the input or None, not crash
        assert decoded is not None

    def test_auto_obfuscate_on_save(self, manager):
        """Test that plain text keys are auto-obfuscated on save."""
        # Set a plain text key
        manager.config["groq_api_key"] = "gsk_plain_text_key"
        manager.save_config()

        # Load from file and verify it's obfuscated
        with open(manager.config_file, "r", encoding="utf-8") as f:
            saved = json.load(f)

        assert not saved["groq_api_key"].startswith("gsk_")


@pytest.mark.unit
class TestLocalization:
    """Tests for localization functionality."""

    @pytest.fixture
    def manager(self):
        """Create a ConfigManager instance."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            config_file = f.name

        manager = ConfigManager(config_file=config_file)
        yield manager

        if os.path.exists(config_file):
            os.unlink(config_file)

    def test_localization_manager_initialized(self, manager):
        """Test that LocalizationManager is initialized."""
        assert manager.localization_manager is not None

    def test_get_localized_string(self, manager):
        """Test getting localized strings."""
        # Mock the localization manager
        manager.localization_manager.get = Mock(return_value="Translated text")

        result = manager.get_localized_string("test_key")

        assert result == "Translated text"
        manager.localization_manager.get.assert_called_once()

    def test_set_language(self, manager):
        """Test setting the language."""
        manager.localization_manager.set_language = Mock()

        manager.set_language("en")

        manager.localization_manager.set_language.assert_called_with("en")
        assert manager.config["default_language"] == "en"


@pytest.mark.unit
class TestEnvironmentVariables:
    """Tests for environment variable handling."""

    def test_get_groq_api_key_from_env(self):
        """Test getting Groq API key from environment variable."""
        with patch.dict(os.environ, {"GROQ_API_KEY": "gsk_env_key_123"}):
            with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
                config_file = f.name

            try:
                manager = ConfigManager(config_file=config_file)
                env_key = manager.get_groq_api_key_from_env()

                assert env_key == "gsk_env_key_123"
            finally:
                if os.path.exists(config_file):
                    os.unlink(config_file)

    def test_get_groq_api_key_from_env_not_set(self):
        """Test getting Groq API key when environment variable is not set."""
        with patch.dict(os.environ, {}, clear=True):
            with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
                config_file = f.name

            try:
                manager = ConfigManager(config_file=config_file)
                env_key = manager.get_groq_api_key_from_env()

                assert env_key is None
            finally:
                if os.path.exists(config_file):
                    os.unlink(config_file)


@pytest.mark.unit
class TestConfigValidation:
    """Tests for configuration validation."""

    @pytest.fixture
    def manager(self):
        """Create a ConfigManager instance."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            config_file = f.name

        manager = ConfigManager(config_file=config_file)
        yield manager

        if os.path.exists(config_file):
            os.unlink(config_file)

    def test_version_always_default(self, manager):
        """Test that app_version is always set to default, even in saved config."""
        # Try to set a different version
        manager.config["app_version"] = "0.12.0"
        manager.save_config()

        # Reload and verify it's back to default
        manager2 = ConfigManager(config_file=manager.config_file)
        assert manager2.config["app_version"] == "0.15.0"

    def test_audio_priority_apps_default(self, manager):
        """Test that audio_priority_apps has default values."""
        apps = manager.get("audio_priority_apps")

        assert isinstance(apps, list)
        assert len(apps) > 0
        assert "zoom.exe" in apps


@pytest.mark.unit
class TestConfigIntegrity:
    """Tests for configuration data integrity."""

    @pytest.fixture
    def manager(self):
        """Create a ConfigManager instance."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            config_file = f.name

        manager = ConfigManager(config_file=config_file)
        yield manager

        if os.path.exists(config_file):
            os.unlink(config_file)

    def test_save_preserves_all_settings(self, manager):
        """Test that saving preserves all configuration settings."""
        # Modify multiple settings
        manager.set("hotkey", "F8")
        manager.set("max_audio_files", 75)
        manager.set("auto_cleanup_enabled", False)
        manager.save_config()

        # Load new instance
        manager2 = ConfigManager(config_file=manager.config_file)

        assert manager2.get("hotkey") == "F8"
        assert manager2.get("max_audio_files") == 75
        assert manager2.get("auto_cleanup_enabled") == False

    def test_multiple_save_load_cycles(self, manager):
        """Test that multiple save/load cycles maintain integrity."""
        original_hotkey = manager.get("hotkey")

        # Save and load 3 times
        for i in range(3):
            manager.set("hotkey", f"F{i}")
            manager.save_config()

            manager2 = ConfigManager(config_file=manager.config_file)
            assert manager2.get("hotkey") == f"F{i}"
            manager = manager2

        # Final verification
        assert manager.get("hotkey") == "F2"
