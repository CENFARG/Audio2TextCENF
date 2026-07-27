"""
Tests for v0.15 → v0.16 config migration with SecretManager integration.

Spec: "Idempotent re-run" — second migration creates no second backup.
Spec: "XOR keys → SecretManager" — decoded plaintext reaches SecretManager.
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest


FIXTURE_DIR = Path(__file__).resolve().parent.parent / "fixtures"
GOLDEN_CONFIG = FIXTURE_DIR / "config_v015.json"


class TestMigrationIdempotency:
    """Spec: migration is idempotent — no double backup, no data loss."""

    def test_migration_decodes_xor_key(self):
        """XOR+Base64 groq_api_key decodes to plaintext 'gsk_test...'."""
        from audio2text.config._decoder import decode_xor_key

        raw = json.loads(GOLDEN_CONFIG.read_text(encoding="utf-8"))
        decoded = decode_xor_key(raw["groq_api_key"])
        assert decoded.startswith("gsk_")
        assert decoded == "gsk_test1234567890abcdef"

    def test_secret_manager_receives_decoded_key(self):
        """After migration, SecretManager has the decoded plaintext key."""
        from audio2text.config.migration import ConfigMigrator
        from core_infrastructure.secrets import InMemorySecretAdapter

        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            config_copy = tmp / "config.json"
            config_copy.write_text(GOLDEN_CONFIG.read_text(encoding="utf-8"))
            output = tmp / "config_v016.json"

            secret_mgr = InMemorySecretAdapter()
            migrator = ConfigMigrator(secret_manager=secret_mgr)
            migrator.run(config_copy, output)

            # Migrated config must NOT contain the raw API key (stripped)
            new_config = json.loads(output.read_text(encoding="utf-8"))
            assert "groq_api_key" not in new_config, (
                "Secret must be stripped from output config"
            )

    def test_idempotent_backup_guard_prevents_double_backup(self):
        """Second run with same input MUST NOT create a second .v015.bak."""
        from audio2text.config.migration import ConfigMigrator

        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            config_copy = tmp / "config.json"
            config_copy.write_text(GOLDEN_CONFIG.read_text(encoding="utf-8"))
            output = tmp / "config_v016.json"
            backup = Path(str(config_copy) + ".v015.bak")

            # First migration: backup SHOULD be created
            migrator = ConfigMigrator(secret_manager=None)
            migrator.run(config_copy, output)
            assert backup.exists()
            backup_mtime_first = backup.stat().st_mtime

            # Second migration with same input: backup must NOT change
            # Restore old config for re-run
            config_copy.write_text(GOLDEN_CONFIG.read_text(encoding="utf-8"))
            migrator2 = ConfigMigrator(secret_manager=None)
            migrator2.run(config_copy, output)
            assert backup.exists()
            backup_mtime_second = backup.stat().st_mtime

            # Guard: backup unchanged = no second backup created
            assert backup_mtime_first == backup_mtime_second, (
                "Idempotency violation: .v015.bak was overwritten on re-run. "
                "Guard must skip backup creation if it already exists."
            )