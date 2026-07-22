"""
Smoke test: verify bootstrap coexists with existing audio2text modules.
Runs as an integration check — real imports, no mocking.
"""


def test_bootstrap_with_existing_modules():
    """Bootstrap imports must not conflict with existing audio2text modules."""
    from audio2text.infrastructure.bootstrap import bootstrap

    registry = bootstrap({"app": {"name": "audio2text"}})

    # Domain models
    from audio2text.domain.transcription import TranscriptionResult  # noqa: F401
    from audio2text.domain.audio import AudioSegment, AudioFormat  # noqa: F401
    from audio2text.domain.metadata import TranscriptionMetadata  # noqa: F401

    # Provider ABC + concrete providers
    from audio2text.providers.base import TranscriptionProvider  # noqa: F401
    from audio2text.providers.groq_provider import GroqProvider  # noqa: F401
    from audio2text.providers.faster_whisper_provider import FasterWhisperProvider  # noqa: F401
    from audio2text.providers.mock_provider import MockProvider  # noqa: F401

    # Config
    from audio2text.config._schema import build_default_config  # noqa: F401
    from audio2text.config.schema import Audio2TextConfig  # noqa: F401

    assert registry.get_config() is not None


def test_all_seven_managers_functional():
    """Exercise every manager through its public API."""
    from audio2text.infrastructure.bootstrap import bootstrap

    registry = bootstrap({"app": {"name": "audio2text", "language": "es_ES"}})

    config = registry.get_config()
    assert config.get_string("app.name") == "audio2text"
    assert config.get_env() in ("local", "dev", "staging", "prod")

    logger = registry.get_logger()
    logger.info("smoke.test", phase="integration")

    secrets = registry.get_secrets()
    secrets.set_secret("smoke_key", "smoke_value")
    import asyncio
    result = asyncio.run(secrets.get_secret("smoke_key"))
    assert result == "smoke_value"

    errors = registry.get_errors()
    try:
        raise RuntimeError("smoke error")
    except RuntimeError as e:
        errors.classify(e)

    obs = registry.get_observability()
    obs.increment_counter("smoke.counter", 1)
    obs.start_span("smoke.span")

    cache = registry.get_cache()
    cache.set("smoke", "value")
    assert cache.get("smoke") == "value"
    assert cache.exists("smoke")

    i18n = registry.get_i18n()
    i18n.set_locale("es_ES")
    title = i18n.t("app.title")
    assert title == "Audio2Text"


def test_migration_decodes_real_key():
    """XOR decoder works with real fixture."""
    from audio2text.config._decoder import decode_xor_key
    import json
    from pathlib import Path

    fixture = Path(__file__).resolve().parent.parent / "fixtures" / "config_v015.json"
    raw = json.loads(fixture.read_text(encoding="utf-8"))
    decoded = decode_xor_key(raw["groq_api_key"])
    assert decoded.startswith("gsk_")


def test_migration_with_secret_manager():
    """ConfigMigrator integrates with core_infrastructure InMemorySecretAdapter."""
    import tempfile, json
    from pathlib import Path
    from core_infrastructure.secrets import InMemorySecretAdapter
    from audio2text.config.migration import ConfigMigrator

    fixture = Path(__file__).resolve().parent.parent / "fixtures" / "config_v015.json"

    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        config_copy = tmp / "config.json"
        config_copy.write_text(fixture.read_text(encoding="utf-8"))
        output = tmp / "config_v016.json"

        secret_mgr = InMemorySecretAdapter()
        migrator = ConfigMigrator(secret_manager=secret_mgr)
        migrator.run(config_copy, output)

        new_config = json.loads(output.read_text(encoding="utf-8"))
        assert "groq_api_key" not in new_config, "Secret leaked to output"

        import asyncio
        decoded = asyncio.run(secret_mgr.get_secret("groq_api_key"))
        assert decoded.startswith("gsk_"), f"Expected gsk_ key, got: {decoded[:10]}..."
