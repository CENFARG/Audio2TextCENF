"""@File: audio2text/config/schema.py
@Description: Audio2Text v0.16 Pydantic config schema model.
    Single source of truth for all configuration fields.
@Version: 0.16.0
@Author: CENF Development Team
@License: Apache-2.0
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class GroqProviderConfig(BaseModel):
    """Groq cloud provider settings."""
    api_key_secret_key: str = "groq_api_key"
    model: str = "whisper-large-v3"
    base_url: str = "https://api.groq.com"
    timeout_s: float = 60.0
    max_retries: int = 3


class FasterWhisperConfig(BaseModel):
    """faster-whisper local provider settings."""
    model_size: str = "base"
    device: str = "auto"
    compute_type: str = "auto"
    models_dir: str = "./models"
    vad_filter: bool = True
    vad_min_silence_ms: int = 500
    beam_size: int = 5
    enabled: bool = False


class NvidiaRivaConfig(BaseModel):
    """NVIDIA Riva provider settings."""
    host: str = "grpc.nvcf.nvidia.com"
    port: int = 443
    use_ssl: bool = True
    api_key_secret_key: str = "nvidia_api_key"
    model: str = "parakeet-1.1b"
    enabled: bool = False
    connection_mode: str = "cloud"


class ProvidersConfig(BaseModel):
    """Transcription provider configuration."""
    primary: str = "groq"
    fallback_chain: list[str] = Field(default_factory=list)
    groq: GroqProviderConfig = Field(default_factory=GroqProviderConfig)
    faster_whisper: FasterWhisperConfig = Field(default_factory=FasterWhisperConfig)
    nvidia_riva: NvidiaRivaConfig = Field(default_factory=NvidiaRivaConfig)


class AudioConfig(BaseModel):
    """Audio capture settings."""
    sample_rate_hz: int = 16000
    channels: int = 1
    buffer_seconds: int = 600
    device_index: int | None = None
    save_recordings: bool = True
    recordings_dir: str = "./audio"
    record_mode: str = "toggle"
    max_recording_time_s: int = 300
    max_audio_files: int = 100
    auto_cleanup_enabled: bool = True


class HotkeyConfig(BaseModel):
    """Hotkey settings."""
    record_toggle: str = "f8"
    cancel: str = "Esc"
    enabled: bool = True


class LocalizationConfig(BaseModel):
    """Localization / i18n settings."""
    language: str = "es_ES"
    fallback: str = "en_US"
    locales_dir: str = "./audio2text/locales"


class HistoryConfig(BaseModel):
    """Transcription history settings."""
    max_entries: int = 100
    cleanup_older_than_days: int = 90
    history_file: str = "./data/history.jsonl"


class VocabularyConfig(BaseModel):
    """Vocabulary file paths."""
    custom_path: str = "./vocabulary/custom.json"
    tech_path: str = "./vocabulary/ia_tech.json"
    general_path: str = "./vocabulary/general.json"


class ContextBlocksConfig(BaseModel):
    """Context blocks settings."""
    enabled: bool = True
    directory: str = "."
    task_extractor_enabled: bool = True
    summary_enabled: bool = True
    keyword_extractor_enabled: bool = True


class AIEnhancementConfig(BaseModel):
    """AI enhancement settings."""
    enabled: bool = True
    default_profile: str = "medium"
    default_provider: str = "groq"
    groq_model: str = "llama-3.1-70b-versatile"
    openai_model: str = "gpt-4o-mini"


class ApiConfig(BaseModel):
    """REST API server settings."""
    host: str = "127.0.0.1"
    port: int = 8765
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:*"])


class UiConfig(BaseModel):
    """UI theme and window settings."""
    theme: str = "system"
    window_width: int = 1100
    window_height: int = 760
    show_overlay: bool = True
    auto_paste: bool = True
    show_transcription_panel: bool = True


class LoggingConfig(BaseModel):
    """Logging settings."""
    profile: str = "production"
    logs_dir: str = "./logs"
    pii_masking: bool = True
    rotate_max_bytes: int = 5242880
    rotate_backup_count: int = 5


class Audio2TextConfig(BaseModel):
    """Root Audio2Text v0.16 configuration model."""
    version: str = "0.16.0"
    providers: ProvidersConfig = Field(default_factory=ProvidersConfig)
    audio: AudioConfig = Field(default_factory=AudioConfig)
    hotkey: HotkeyConfig = Field(default_factory=HotkeyConfig)
    localization: LocalizationConfig = Field(default_factory=LocalizationConfig)
    history: HistoryConfig = Field(default_factory=HistoryConfig)
    vocabulary: VocabularyConfig = Field(default_factory=VocabularyConfig)
    context_blocks: ContextBlocksConfig = Field(default_factory=ContextBlocksConfig)
    ai_enhancement: AIEnhancementConfig = Field(default_factory=AIEnhancementConfig)
    api: ApiConfig = Field(default_factory=ApiConfig)
    ui: UiConfig = Field(default_factory=UiConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    startup: bool = False
    sounds_enabled: bool = True
