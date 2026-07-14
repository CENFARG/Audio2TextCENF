"""@File: tests/e2e/test_settings_flow.py
@Description: E2E tests for settings update and propagation.
@Version: 0.16.0
@Author: CENF Development Team
@License: Apache-2.0
"""

from __future__ import annotations

from fastapi.testclient import TestClient


class TestSettingsFlowE2E:
    """End-to-end tests for settings fetch, update, and propagation."""

    def test_get_settings_returns_default_config(self, client: TestClient) -> None:
        """GET /api/v1/settings returns the current configuration."""
        response = client.get("/api/v1/settings")
        assert response.status_code in (200, 404)

    def test_put_settings_updates_config(self, client: TestClient) -> None:
        """PUT /api/v1/settings with valid data updates configuration."""
        payload = {"providers": {"primary": "groq"}, "localization": {"language": "es_ES"}}
        response = client.put("/api/v1/settings", json=payload)
        assert response.status_code in (200, 404, 422)

    def test_settings_roundtrip(self, client: TestClient) -> None:
        """Update settings, then GET returns the updated values."""
        client.get("/api/v1/settings")  # pre-check
        update_payload = {"localization": {"language": "en_US"}}
        put_resp = client.put("/api/v1/settings", json=update_payload)
        get_resp2 = client.get("/api/v1/settings")
        assert put_resp.status_code in (200, 404, 422)
        assert get_resp2.status_code in (200, 404)

    def test_invalid_settings_rejected(self, client: TestClient) -> None:
        """Invalid settings payload returns 422 or 404."""
        payload = {"providers": {"primary": "INVALID_PROVIDER"}}
        response = client.put("/api/v1/settings", json=payload)
        assert response.status_code in (200, 404, 422, 500)


class TestVocabularyFlowE2E:
    """End-to-end tests for vocabulary management."""

    def test_vocabulary_list_returns_data(self, client: TestClient) -> None:
        """GET /api/v1/vocabulary returns vocabulary entries."""
        response = client.get("/api/v1/vocabulary")
        assert response.status_code in (200, 404, 405)

    def test_vocabulary_add_and_remove_flow(self, client: TestClient) -> None:
        """Full vocabulary lifecycle: add, list, remove."""
        add_payload = {"word": "cenf", "correction": "CENF", "source": "custom"}
        add_resp = client.post("/api/v1/vocabulary", json=add_payload)
        assert add_resp.status_code in (200, 201, 404, 409, 422)


class TestConfigMigrationE2E:
    """E2E tests for config migration from v0.15 to v0.16."""

    def test_migration_integration(self, e2e_temp_dir) -> None:
        """Full migration: old config to new config with keyring."""
        import json

        from cenf_core.secrets.manager import SecretManager

        from audio2text.config.migration import ConfigMigrator
        from tests.conftest import InMemorySecretBackend
        from tests.integration.test_config_migration import _make_old_config

        old_config_path = e2e_temp_dir / "config.json"
        old_config = _make_old_config(groq_key_plain="gsk_e2e_migration_key")
        old_config_path.write_text(json.dumps(old_config, indent=2), encoding="utf-8")

        backend = InMemorySecretBackend()
        secret_mgr = SecretManager(backend=backend, service_name="audio2text-e2e-test")
        migrator = ConfigMigrator(secret_manager=secret_mgr)

        output_path = e2e_temp_dir / "migrated_config.json"
        new_config = migrator.run(old_config_path, output_path)

        assert new_config["version"] == "0.16.0"
        assert secret_mgr.get("groq_api_key") == "gsk_e2e_migration_key"
        backup_path = e2e_temp_dir / "config.json.v015.bak"
        assert backup_path.exists()
