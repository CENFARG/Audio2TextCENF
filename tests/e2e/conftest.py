"""@File: tests/e2e/conftest.py
@Description: Shared fixtures for E2E tests — FastAPI TestClient with mocked services.
@Version: 0.16.0
@Author: CENF Development Team
@License: Apache-2.0
"""

from __future__ import annotations

import datetime
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from tests.conftest import InMemorySecretBackend


@pytest.fixture
def app() -> FastAPI:
    """Return a fully configured FastAPI app (with mocked services)."""
    from unittest.mock import patch

    with patch("audio2text.api.lifespan._init_services"), patch(
        "audio2text.api.lifespan._shutdown_services"
    ):
        from audio2text.api.app import create_app

        return create_app()


@pytest.fixture
def client(app: FastAPI) -> TestClient:
    """Return a TestClient for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
def secret_backend() -> InMemorySecretBackend:
    """In-memory secret backend for E2E tests."""
    return InMemorySecretBackend()


@pytest.fixture
def e2e_temp_dir(tmp_path: Path) -> Path:
    """Temporary directory for E2E test artifacts."""
    return tmp_path


@pytest.fixture
def mock_transcription_result() -> MagicMock:
    """Return a mock TranscriptionResult for use in E2E flows."""
    result = MagicMock()
    result.text = "E2E test transcription result with spanish accents: canción and niño"
    result.duration_seconds = 2.5
    result.language = "es"
    result.confidence = 0.97
    result.provider_name = "mock"
    result.model_name = "mock-e2e"
    result.segments = []
    result.created_at = datetime.datetime(2026, 5, 12, tzinfo=datetime.timezone.utc)
    return result
