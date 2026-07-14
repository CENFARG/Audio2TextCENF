"""@File: tests/integration/test_config_migration.py
@Description: Integration tests for config migration from v0.15 XOR format to v0.16.
@Version: 0.16.0
@Author: CENF Development Team
@License: Apache-2.0
"""

from __future__ import annotations

import base64
import json
from pathlib import Path

import pytest

from tests.conftest import InMemorySecretBackend

# ---------------------------------------------------------------------------
# Helpers — XOR encoding (matching the old backend/config_manager.py logic)
# ---------------------------------------------------------------------------

_XOR_KEY = "CENF_SECRET"


def _xor_encode(plain: str) -> str:
    """Encode a string using the old XOR+Base64 method."""
    xor_bytes = bytes(
        ord(c) ^ ord(_XOR_KEY[i % len(_XOR_KEY)]) for i, c in enumerate(plain)
    )
    return base64.b64encode(xor_bytes).decode("utf-8")


def _xor_decode(encoded: str) -> str:
    """Decode an XOR+Base64 obfuscated string."""
    if not encoded:
        return ""
    if encoded.startswith(("gsk_", "sk-", "nvapi-")):
        return encoded
    try:
        decoded_bytes = base64.b64decode(encoded)
        result = "".join(
            chr(b ^ ord(_XOR_KEY[i % len(_XOR_KEY)]))
            for i, b in enumerate(decoded_bytes)
        )
        if not result.startswith(("gsk_", "sk-", "nvapi-")):
            return encoded
        return result
    except Exception:
        return encoded


def _make_old_config(groq_key_plain: str = "gsk_test_migration_key_12345") -> dict:
    """Build a representative old-style config.json dict."""
    return {
        "app_version": "0.15.1",
        "audio_path": "./audio",
        "transcriptions_path": "./transcriptions",
        "save_audio": True,
        "save_logs": True,
        "hotkey": "f9",
        "hotkey_modifier": "",
        "record_mode": "toggle",
        "default_language": "en",
        "max_audio_files": 50,
        "max_log_entries": 500,
        "max_recording_time": 120,
        "max_transcription_age_days": 14,
        "auto_cleanup_enabled": False,
        "groq_api_key": _xor_encode(groq_key_plain),
        "gift_key_encoded": _xor_encode(groq_key_plain),
        "nvidia_api_key": _xor_encode("nvapi-test-key-67890"),
        "audio_priority_apps": ["zoom.exe"],
        "show_transcription_panel": True,
        "auto_paste_text": False,
        "client_logo_path": "",
        "utf8_validation": True,
        "asr_provider": "faster_whisper",
        "nvidia_enabled": True,
        "nvidia_mode": "cloud",
        "faster_whisper_enabled": True,
        "faster_whisper_model": "large-v3",
        "faster_whisper_device": "cuda",
        "autostart_windows": True,
        "tutorial_completed": True,
        "use_post_processing": False,
        "use_llm_post_processing": False,
        "post_processing_model": "llama-3.3-70b-versatile",
        "blocks": {
            "task_extractor_enabled": False,
            "summary_enabled": False,
            "keyword_extractor_enabled": False,
        },
        "window_geometry": "563x450+78+78",
    }


# ---------------------------------------------------------------------------
# Fixture: SecretManager for migration tests
# ---------------------------------------------------------------------------


@pytest.fixture
def secret_backend() -> InMemorySecretBackend:
    """In-memory backend for storing migrated secrets."""
    return InMemorySecretBackend()


@pytest.fixture
def temp_old_config(tmp_path: Path) -> Path:
    """Create a temporary old-style config.json."""
    config_path = tmp_path / "config.json"
    old_config = _make_old_config()
    config_path.write_text(json.dumps(old_config, indent=2), encoding="utf-8")
    return config_path


# ---------------------------------------------------------------------------
# RED phase tests — ConfigMigrator does NOT exist yet
# ---------------------------------------------------------------------------


class TestConfigMigration:
    """Integration tests for the config migrator (v0.15 → v0.16)."""

    def test_detect_old_config_returns_true_for_v015(self, temp_old_config: Path) -> None:
        """Given a v0.15 config.json, detection returns True."""
        from audio2text.config.migration import ConfigMigrator

        migrator = ConfigMigrator()
        result = migrator.detect_old_config(temp_old_config)
        assert result is True

    def test_detect_old_config_returns_false_for_v016(self, tmp_path: Path) -> None:
        """Given a v0.16 config, detection returns False."""
        from audio2text.config.migration import ConfigMigrator

        v016_config = tmp_path / "config.json"
        v016_config.write_text(
            json.dumps({"version": "0.16.0", "providers": {"primary": "groq"}}),
            encoding="utf-8",
        )
        migrator = ConfigMigrator()
        result = migrator.detect_old_config(v016_config)
        assert result is False

    def test_migrate_keys_decodes_xor_and_saves_to_keyring(
        self, temp_old_config: Path, secret_backend: InMemorySecretBackend
    ) -> None:
        """XOR-encoded keys are decoded and stored in SecretManager."""
        from cenf_core.secrets.manager import SecretManager

        from audio2text.config.migration import ConfigMigrator

        secret_mgr = SecretManager(
            backend=secret_backend,
            service_name="audio2text-migration-test",
        )
        migrator = ConfigMigrator(secret_manager=secret_mgr)

        migrated_keys = migrator.migrate_keys(temp_old_config)

        assert "groq_api_key" in migrated_keys
        assert "nvidia_api_key" in migrated_keys
        assert secret_mgr.get("groq_api_key") == "gsk_test_migration_key_12345"
        assert secret_mgr.get("nvidia_api_key") == "nvapi-test-key-67890"

    def test_migrate_settings_maps_old_to_new_schema(self, temp_old_config: Path) -> None:
        """Old flat keys are mapped to the new nested Pydantic schema."""
        from audio2text.config.migration import ConfigMigrator

        migrator = ConfigMigrator()
        new_config = migrator.migrate_settings(temp_old_config)

        # Top-level version
        assert new_config["version"] == "0.16.0"

        # Language mapping: default_language → localization.language
        # Old short codes: "es" → "es_ES", "en" → "en_US"
        assert new_config["localization"]["language"] == "en_US"

        # Hotkey mapping: hotkey → hotkey.record_toggle
        assert new_config["hotkey"]["record_toggle"] == "f9"

        # Provider mapping: asr_provider → providers.primary
        assert new_config["providers"]["primary"] == "faster_whisper"

        # faster_whisper settings
        fw = new_config["providers"]["faster_whisper"]
        assert fw["model_size"] == "large-v3"
        assert fw["device"] == "cuda"

        # Audio settings
        assert new_config["audio"]["recordings_dir"] == "./audio"
        assert new_config["audio"]["save_recordings"] is True

        # History settings
        assert new_config["history"]["max_entries"] == 50
        assert new_config["history"]["cleanup_older_than_days"] == 14

        # UI settings
        assert new_config["ui"]["show_overlay"] is True

    def test_config_migrator_creates_backup(
        self, temp_old_config: Path, tmp_path: Path
    ) -> None:
        """Migration creates a backup of the old config.json."""
        from audio2text.config.migration import ConfigMigrator

        migrator = ConfigMigrator()
        output_path = tmp_path / "new_config.json"
        migrator.run(temp_old_config, output_path)

        backup_path = Path(str(temp_old_config) + ".v015.bak")
        assert backup_path.exists(), f"Backup not created at {backup_path}"
        # Backup content matches original
        backup_data = json.loads(backup_path.read_text(encoding="utf-8"))
        assert backup_data["app_version"] == "0.15.1"

    def test_dry_run_preview_does_not_modify_files(
        self, temp_old_config: Path, secret_backend: InMemorySecretBackend
    ) -> None:
        """Dry run reports what would change without modifying anything."""
        from cenf_core.secrets.manager import SecretManager

        from audio2text.config.migration import ConfigMigrator

        secret_mgr = SecretManager(
            backend=secret_backend,
            service_name="audio2text-migration-test",
        )
        migrator = ConfigMigrator(secret_manager=secret_mgr)

        preview = migrator.dry_run(temp_old_config)

        assert isinstance(preview, dict)
        assert "secrets_to_migrate" in preview
        assert "settings_to_map" in preview
        assert "groq_api_key" in preview["secrets_to_migrate"]
        # Dry run should NOT write to keyring
        assert secret_mgr.get("groq_api_key") is None
        # Dry run should NOT create backup
        backup_path = Path(str(temp_old_config) + ".v015.bak")
        assert not backup_path.exists()

    def test_migration_strips_secrets_from_output_config(
        self, temp_old_config: Path, secret_backend: InMemorySecretBackend, tmp_path: Path
    ) -> None:
        """The output config.json MUST NOT contain any API keys."""
        from cenf_core.secrets.manager import SecretManager

        from audio2text.config.migration import ConfigMigrator

        secret_mgr = SecretManager(
            backend=secret_backend,
            service_name="audio2text-migration-test",
        )
        migrator = ConfigMigrator(secret_manager=secret_mgr)
        output_path = tmp_path / "migrated_config.json"
        migrator.run(temp_old_config, output_path)

        output_data = json.loads(output_path.read_text(encoding="utf-8"))
        # Flatten and check no API keys exist
        output_str = json.dumps(output_data)
        assert "gsk_" not in output_str
        assert "nvapi-" not in output_str
        assert "JDYl" not in output_str  # base64 XOR marker
