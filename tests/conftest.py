"""
Pytest configuration and shared fixtures for Audio2Text testing.

This module provides common fixtures and configuration for all test modules.
It sets up test data, mocks, and test environment.

Author: Audio2Text Development Team
Version: 0.13.0
"""

import pytest
import sys
import os
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch
import numpy as np

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture
def project_root_path():
    """Return the project root path."""
    return project_root


@pytest.fixture
def test_data_dir(project_root_path):
    """Return the test data directory path."""
    test_data = project_root_path / "tests" / "data"
    test_data.mkdir(exist_ok=True)
    return test_data


@pytest.fixture
def temp_audio_file(test_data_dir):
    """Create a temporary WAV audio file for testing.

    Returns:
        Path: Path to temporary audio file
    """
    import wave

    audio_file = test_data_dir / "test_audio.wav"

    # Create a simple WAV file (1 second of silence at 16000 Hz)
    with wave.open(str(audio_file), "wb") as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 2 bytes (16-bit)
        wav_file.setframerate(16000)  # 16 kHz sample rate

        # Write 1 second of silence
        silence = b"\x00\x00" * 16000
        wav_file.writeframes(silence)

    yield audio_file

    # Cleanup
    if audio_file.exists():
        audio_file.unlink()


@pytest.fixture
def mock_config():
    """Create a mock configuration dictionary.

    Returns:
        dict: Mock configuration
    """
    return {
        "version": "0.13.0",
        "api_key": "test_api_key_123",
        "api_key_obfuscated": " obscured_key",
        "language": "es",
        "model": "whisper-large-v3",
        "hotkey": "F5",
        "output_dir": "transcriptions",
        "max_history_items": 100,
        "auto_cleanup_days": 30,
        "theme": "dark",
        "service": "groq",
        "faster_whisper": {"model_size": "base", "device": "cpu", "compute_type": "int8"},
        "blocks": {
            "task_extractor": {"enabled": True, "stage": "post"},
            "summary": {"enabled": True, "stage": "post"},
            "keyword_extractor": {"enabled": True, "stage": "post"},
        },
        "vocabulary": {"custom_corrections": {"CENF": "zenf", "Prompt": "prompt"}},
    }


@pytest.fixture
def mock_config_file(test_data_dir, mock_config):
    """Create a temporary config file for testing.

    Returns:
        Path: Path to temporary config file
    """
    config_file = test_data_dir / "test_config.json"
    with open(config_file, "w", encoding="utf-8") as f:
        json.dump(mock_config, f, indent=2, ensure_ascii=False)

    yield config_file

    # Cleanup
    if config_file.exists():
        config_file.unlink()


@pytest.fixture
def mock_transcriber():
    """Create a mock Transcriber object with mocked dependencies.

    Returns:
        Mock: Mocked Transcriber object
    """
    transcriber = Mock()
    transcriber.api_key = "test_api_key"
    transcriber.service = "groq"
    transcriber.language = "es"
    transcriber.model = "whisper-large-v3"
    transcriber.is_recording = False

    # Mock methods
    transcriber.transcribe = Mock(
        return_value={"text": "Este es un texto de prueba.", "language": "es", "duration": 1.5}
    )

    transcriber.start_recording = Mock()
    transcriber.stop_recording = Mock()
    transcriber.save_transcription = Mock()

    return transcriber


@pytest.fixture
def mock_groq_response():
    """Create a mock Groq API response.

    Returns:
        dict: Mock Groq response
    """
    return {
        "text": "Esta es una transcripción de prueba.",
        "language": "es",
        "duration": 2.5,
        "words": [
            {"word": "Esta", "start": 0.0, "end": 0.2},
            {"word": "es", "start": 0.2, "end": 0.4},
            {"word": "una", "start": 0.4, "end": 0.6},
            {"word": "transcripción", "start": 0.6, "end": 1.2},
            {"word": "de", "start": 1.2, "end": 1.4},
            {"word": "prueba", "start": 1.4, "end": 1.8},
        ],
    }


@pytest.fixture
def mock_llm_response():
    """Create a mock LLM metadata response.

    Returns:
        dict: Mock LLM metadata response
    """
    return {
        "summary": "Resumen de prueba",
        "tasks": ["Tarea 1", "Tarea 2"],
        "keywords": ["palabra1", "palabra2"],
        "category": "General",
    }


@pytest.fixture
def temp_transcription_dir(tmp_path):
    """Create a temporary transcription directory.

    Returns:
        Path: Temporary directory path
    """
    trans_dir = tmp_path / "transcriptions"
    trans_dir.mkdir(exist_ok=True)
    return trans_dir


@pytest.fixture
def sample_transcription(temp_transcription_dir):
    """Create a sample transcription file.

    Returns:
        Path: Path to sample transcription file
    """
    trans_file = temp_transcription_dir / "2023-01-01_120000.txt"
    content = """Fecha: 2023-01-01 12:00:00
Duración: 1.5 segundos
Idioma: es
Servicio: groq

Texto:
Esta es una transcripción de prueba para el sistema de testing.
"""
    trans_file.write_text(content, encoding="utf-8")
    return trans_file


@pytest.fixture
def mock_audio_data():
    """Create mock audio data as numpy array.

    Returns:
        np.ndarray: Mock audio data (1 second at 16kHz)
    """
    # 1 second of silence at 16kHz
    return np.zeros(16000, dtype=np.int16)


@pytest.fixture
def secret_manager():
    """In-memory secret manager with get/set API (test helper).

    Mirrors cenf_core.secrets.manager.SecretManager contract used by
    GroqProvider.validate_config when no key is stored.
    """
    class _MemSecretManager:
        def __init__(self):
            self._store: dict[str, str] = {}

        def set(self, key: str, value: str) -> None:
            self._store[key] = value

        def get(self, key: str, default: str | None = None) -> str | None:
            return self._store.get(key, default)

    return _MemSecretManager()


@pytest.fixture
def mock_hotkey_combination():
    """Create a mock hotkey combination.

    Returns:
        dict: Mock hotkey combination
    """
    return {"key": "F5", "modifiers": [], "action": "start_stop_recording"}


@pytest.fixture
def mock_metadata():
    """Create mock metadata for a transcription.

    Returns:
        dict: Mock metadata
    """
    return {
        "date": "2023-01-01 12:00:00",
        "duration": 1.5,
        "language": "es",
        "service": "groq",
        "summary": "Resumen generado por LLM",
        "tasks": ["Revisar documentación", "Actualizar código"],
        "keywords": ["testing", "desarrollo"],
        "category": "Desarrollo",
    }


# Pytest hooks for custom configuration


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line("markers", "unit: Unit tests (fast, isolated)")
    config.addinivalue_line("markers", "integration: Integration tests (slower)")
    config.addinivalue_line("markers", "slow: Slow tests (> 1 second)")
    config.addinivalue_line("markers", "api: Tests requiring API access")


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add default markers."""
    for item in items:
        # Mark all tests in test_*.py files as unit tests by default
        if "test_" in item.fspath.basename:
            if not any(
                mark.name in ["unit", "integration", "slow", "api"] for mark in item.iter_markers()
            ):
                item.add_marker(pytest.mark.unit)
