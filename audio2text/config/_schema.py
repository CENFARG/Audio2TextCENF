"""@File: audio2text/config/_schema.py
@Description: v0.16 config schema defaults, key mapping, and nested dict helpers.
@Version: 0.16.0
@Author: CENF Development Team
@License: Apache-2.0
"""

from __future__ import annotations

from typing import Any

# Field mapping: old v0.15 flat keys → new v0.16 nested Pydantic schema
_KEY_MAPPING: dict[str, str] = {
    "default_language": "localization.language",
    "hotkey": "hotkey.record_toggle",
    "asr_provider": "providers.primary",
    "faster_whisper_model": "providers.faster_whisper.model_size",
    "faster_whisper_device": "providers.faster_whisper.device",
    "audio_path": "audio.recordings_dir",
    "save_audio": "audio.save_recordings",
    "max_audio_files": "history.max_entries",
    "max_transcription_age_days": "history.cleanup_older_than_days",
    "max_recording_time": "audio.buffer_seconds",
    "show_transcription_panel": "ui.show_overlay",
    "auto_paste_text": "ui.auto_paste",
    "nvidia_enabled": "providers.nvidia_riva.enabled",
    "nvidia_mode": "providers.nvidia_riva.connection_mode",
    "faster_whisper_enabled": "providers.faster_whisper.enabled",
    "autostart_windows": "startup",
}

# Which keys in the old config contain XOR-obfuscated secrets
_SECRET_KEYS: list[str] = ["groq_api_key", "nvidia_api_key", "gift_key_encoded"]


def build_default_config() -> dict[str, Any]:
    """Return a skeleton v0.16 config with sensible defaults."""
    return {
        "version": "0.16.0",
        "providers": {
            "primary": "groq",
            "fallback_chain": [],
            "groq": {
                "api_key_secret_key": "groq_api_key",
                "model": "whisper-large-v3",
                "base_url": "https://api.groq.com",
                "timeout_s": 60.0,
                "max_retries": 3,
            },
            "faster_whisper": {
                "model_size": "base",
                "device": "auto",
                "compute_type": "auto",
                "models_dir": "./models",
                "vad_filter": True,
                "vad_min_silence_ms": 500,
                "beam_size": 5,
                "enabled": False,
            },
            "nvidia_riva": {
                "host": "grpc.nvcf.nvidia.com",
                "port": 443,
                "use_ssl": True,
                "api_key_secret_key": "nvidia_api_key",
                "model": "parakeet-1.1b",
                "enabled": False,
                "connection_mode": "cloud",
            },
        },
        "audio": {
            "sample_rate_hz": 16000,
            "channels": 1,
            "buffer_seconds": 600,
            "device_index": None,
            "save_recordings": True,
            "recordings_dir": "./audio",
        },
        "hotkey": {
            "record_toggle": "f8",
            "cancel": "Esc",
            "enabled": True,
        },
        "localization": {
            "language": "es_ES",
            "fallback": "en_US",
            "locales_dir": "./audio2text/locales",
        },
        "history": {
            "max_entries": 100,
            "cleanup_older_than_days": 90,
            "history_file": "./data/history.jsonl",
        },
        "vocabulary": {
            "custom_path": "./vocabulary/custom.json",
            "tech_path": "./vocabulary/ia_tech.json",
            "general_path": "./vocabulary/general.json",
        },
        "blocks": {
            "enabled": [],
            "blocks_dir": "./blocks",
        },
        "context_blocks": {
            "enabled": True,
            "directory": ".",
        },
        "ai_enhancement": {
            "enabled": True,
            "default_profile": "medium",
            "default_provider": "groq",
            "groq_model": "llama-3.1-70b-versatile",
            "openai_model": "gpt-4o-mini",
        },
        "api": {
            "host": "127.0.0.1",
            "port": 8765,
            "cors_origins": ["http://localhost:*"],
        },
        "ui": {
            "theme": "system",
            "window_width": 1100,
            "window_height": 760,
            "show_overlay": True,
            "auto_paste": True,
        },
        "logging": {
            "profile": "production",
            "logs_dir": "./logs",
            "pii_masking": True,
            "rotate_max_bytes": 5242880,
            "rotate_backup_count": 5,
        },
        "startup": False,
        "sounds_enabled": True,
    }


def apply_mapped_fields(
    raw: dict[str, Any], new_config: dict[str, Any]
) -> None:
    """Apply the key mapping: old flat key → new nested key."""
    for old_key, new_path in _KEY_MAPPING.items():
        if old_key not in raw:
            continue
        value = raw[old_key]
        _set_nested(new_config, new_path, value)


def apply_extra_fields(
    raw: dict[str, Any], new_config: dict[str, Any]
) -> None:
    """Handle fields that need special transformation."""
    # old "record_mode" → toggle/hold
    if raw.get("record_mode") == "hold":
        new_config["hotkey"]["enabled"] = False  # hold mode changes behavior

    # old language: "es" → "es_ES", "en" → "en_US"
    lang = new_config["localization"]["language"]
    if lang == "es":
        new_config["localization"]["language"] = "es_ES"
    elif lang == "en":
        new_config["localization"]["language"] = "en_US"


def _set_nested(data: dict[str, Any], path: str, value: Any) -> None:
    """Set a value in a nested dict using dot-notation path."""
    parts = path.split(".")
    current: Any = data
    for part in parts[:-1]:
        if part not in current:
            current[part] = {}
        current = current[part]
    current[parts[-1]] = value
