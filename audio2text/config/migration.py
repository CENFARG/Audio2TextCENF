"""@File: audio2text/config/migration.py
@Description: ConfigMigrator — v0.15 → v0.16 config migration with XOR key decryption.
@Version: 0.16.0
@Author: CENF Development Team
@License: Apache-2.0
"""

from __future__ import annotations

import json
import logging
import shutil
from pathlib import Path
from typing import Any

from audio2text.config._decoder import decode_xor_key
from audio2text.config._schema import (
    _SECRET_KEYS,
    apply_extra_fields,
    apply_mapped_fields,
    build_default_config,
)

logger = logging.getLogger(__name__)


class ConfigMigrator:
    """Migrates Audio2Text configuration from v0.15 XOR format to v0.16 schema.

    Workflow:
        1. ``detect_old_config()`` — check if the file is old format.
        2. ``migrate_keys()`` — decode XOR secrets, save to SecretManager (keyring).
        3. ``migrate_settings()`` — map flat keys to nested v0.16 schema.
        4. ``run()`` — execute all steps and write the new config.
        5. ``dry_run()`` — preview what will change without modifying anything.
    """

    def __init__(
        self,
        secret_manager: Any | None = None,
    ) -> None:
        """Initialize the ConfigMigrator.

        Args:
            secret_manager: A cenf-core SecretManager instance for keyring storage.
                           If None, secrets are returned in the mapping dict but
                           not persisted.
        """
        self._secret_manager = secret_manager

    # ------------------------------------------------------------------
    # Detection
    # ------------------------------------------------------------------

    def detect_old_config(self, config_path: Path) -> bool:
        """Detect if the file is a v0.15 (or older) config format.

        Heuristic: the root dict contains ``groq_api_key`` which the
        v0.16 schema never puts at root level.

        Args:
            config_path: Path to the config file.

        Returns:
            True if the config appears to be old format.
        """
        if not config_path.exists():
            return False
        try:
            raw = json.loads(config_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return False
        # v0.16 uses nested "providers.primary" — never has "groq_api_key" at root
        return "groq_api_key" in raw and "providers" not in raw

    # ------------------------------------------------------------------
    # Key migration
    # ------------------------------------------------------------------

    def migrate_keys(self, config_path: Path) -> dict[str, str]:
        """Decode XOR-obfuscated keys and store them in SecretManager.

        Args:
            config_path: Path to the old config.json.

        Returns:
            Dict mapping secret key names to their decoded values.
        """
        raw = json.loads(config_path.read_text(encoding="utf-8"))
        migrated: dict[str, str] = {}

        for secret_key in _SECRET_KEYS:
            encoded_value = raw.get(secret_key, "")
            if not encoded_value:
                continue
            decoded = decode_xor_key(encoded_value)
            # Only keep keys that decoded to valid-looking values
            if decoded and decoded != encoded_value:
                keyring_key = secret_key
                migrated[keyring_key] = decoded
                if self._secret_manager is not None:
                    self._secret_manager.set_secret(keyring_key, decoded)
                    logger.info("Migrated secret '%s' to keyring.", keyring_key)

        return migrated

    # ------------------------------------------------------------------
    # Settings migration
    # ------------------------------------------------------------------

    def migrate_settings(self, config_path: Path) -> dict[str, Any]:
        """Map old flat config keys to the new v0.16 nested schema.

        Secrets are stripped from the output — they belong in the keyring.

        Args:
            config_path: Path to the old config.json.

        Returns:
            A dict matching the v0.16 Audio2TextConfig schema shape.
        """
        raw = json.loads(config_path.read_text(encoding="utf-8"))
        new_config: dict[str, Any] = build_default_config()

        apply_mapped_fields(raw, new_config)
        apply_extra_fields(raw, new_config)

        return new_config

    # ------------------------------------------------------------------
    # Full migration
    # ------------------------------------------------------------------

    def run(
        self,
        old_config_path: Path,
        output_config_path: Path,
    ) -> dict[str, Any]:
        """Execute the complete migration workflow.

        1. Validate old format.
        2. Create backup.
        3. Migrate secrets to keyring.
        4. Migrate settings to new schema.
        5. Write new config.json (no secrets).

        Args:
            old_config_path: Path to the v0.15 config.json.
            output_config_path: Where to write the v0.16 config.json.

        Returns:
            The migrated configuration dict (secrets excluded).

        Raises:
            FileNotFoundError: If old_config_path does not exist.
            ValueError: If the file is not old format.
        """
        if not old_config_path.exists():
            raise FileNotFoundError(f"Config file not found: {old_config_path}")

        if not self.detect_old_config(old_config_path):
            raise ValueError(
                f"File at {old_config_path} does not appear to be old format "
                "(missing 'groq_api_key' at root). Already migrated?"
            )

        # 1. Create backup (idempotent: skip if already exists)
        backup_path = Path(str(old_config_path) + ".v015.bak")
        if not backup_path.exists():
            shutil.copy2(str(old_config_path), str(backup_path))
            logger.info("Backup created: %s", backup_path)
        else:
            logger.info("Backup already exists — skipping: %s", backup_path)

        # 2. Migrate secrets to keyring
        self.migrate_keys(old_config_path)

        # 3. Map settings
        new_config = self.migrate_settings(old_config_path)

        # 4. Write new config (no secrets)
        output_config_path.parent.mkdir(parents=True, exist_ok=True)
        output_config_path.write_text(
            json.dumps(new_config, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        logger.info("Migrated config written to %s", output_config_path)

        return new_config

    # ------------------------------------------------------------------
    # Dry run / preview
    # ------------------------------------------------------------------

    def dry_run(self, config_path: Path) -> dict[str, Any]:
        """Preview what would change without modifying anything.

        Args:
            config_path: Path to the old config.json.

        Returns:
            A dict with ``secrets_to_migrate`` and ``settings_to_map`` keys.
        """
        raw = json.loads(config_path.read_text(encoding="utf-8"))

        secrets_preview: dict[str, str] = {}
        for secret_key in _SECRET_KEYS:
            encoded_value = raw.get(secret_key, "")
            if encoded_value:
                decoded = decode_xor_key(encoded_value)
                if decoded and decoded != encoded_value:
                    secrets_preview[secret_key] = f"{decoded[:6]}..."  # masked

        settings_preview = self.migrate_settings(config_path)

        return {
            "secrets_to_migrate": secrets_preview,
            "settings_to_map": settings_preview,
        }
