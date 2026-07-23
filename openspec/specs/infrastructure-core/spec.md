# Infrastructure Core Specification

## Purpose

Define the cross-cutting infrastructure layer for Audio2Text v2 by adopting
`core-cenf-py@v0.1.0` as the sole infrastructure foundation. All legacy
config loaders, ad-hoc loggers, XOR obfuscation, manual error handling,
metrics, caching, and localization MUST be replaced by core-cenf managers
wired through a single `BootstrapOrchestrator`. No business module MAY
import infrastructure adapters directly — it MUST depend on Protocols.

## Requirements

### Requirement: Bootstrap Wiring Order

The system SHALL provide a `BootstrapOrchestrator` in
`audio2text/infrastructure/bootstrap.py` that instantiates core-cenf managers
in a deterministic order. The order MUST be: `ConfigManager` →
`LoggerManager` → `SecretManager` → `ErrorHandlingManager` →
`ObservabilityManager` → remaining managers. Any manager whose constructor
depends on another manager MUST be created after its dependency.

#### Scenario: Bootstrap initializes all managers in order

- GIVEN a valid `config.toml` exists at the configured path
- WHEN `BootstrapOrchestrator().bootstrap()` is invoked
- THEN the orchestrator returns a registry with all 18 managers instantiated
- AND `ConfigManager` is created before `LoggerManager`
- AND `LoggerManager` is created before `SecretManager`

#### Scenario: Bootstrap halts on config failure

- GIVEN `config.toml` is missing or unreadable
- WHEN `BootstrapOrchestrator().bootstrap()` is invoked
- THEN a `ConfigError` is raised before any other manager is created
- AND no manager instance is left in a half-initialized state

### Requirement: ConfigManager Replaces Legacy Loading

The system MUST source all configuration through the core-cenf
`ConfigManager` Protocol. Direct JSON reads, `json.load(config.json)`, and
the legacy `ConfigManager` class MUST NOT exist in `audio2text/`.

#### Scenario: Service reads config via injected ConfigManager

- GIVEN a service constructor receives a `ConfigManager` instance
- WHEN the service requests `providers.primary`
- THEN it receives the configured provider string (e.g., `"groq"`)
- AND no service file contains `json.load`

### Requirement: SecretManager Replaces XOR Obfuscation

The system SHALL store API keys exclusively through the core-cenf
`SecretManager` (backed by the OS keyring). XOR+Base64 obfuscation MUST be
used only inside the one-shot migration decoder, never at read time.

#### Scenario: Provider reads API key from SecretManager

- GIVEN `SecretManager.set("groq_api_key", "gsk_real")` was called
- WHEN `GroqProvider` initializes with the injected SecretManager
- THEN the provider retrieves the plaintext key and is available
- AND the config file on disk contains no API key value

### Requirement: Error Handling Decorator

Every public service method SHALL be wrapped with the core-cenf
`@handle_errors` decorator sourced from `ErrorHandlingManager`. The
decorator MUST convert exceptions into structured error responses and emit
an observability span.

#### Scenario: Service method raises

- GIVEN `TranscriptionService.transcribe` is decorated with `@handle_errors`
- WHEN the provider raises `TimeoutError` mid-call
- THEN a structured `ErrorResult` is returned instead of an unhandled raise
- AND a span tagged `error=true` is recorded by `ObservabilityManager`

### Requirement: Observability for Metrics and Tracing

The system MUST emit, via `ObservabilityManager`, a span per transcription
job with `provider`, `language`, `duration_seconds`, and `status`
attributes. Metrics MUST be queryable for the v2 health endpoint.

#### Scenario: Transcription emits RED metrics

- GIVEN a completed transcription of a 4-second clip
- WHEN the job finishes successfully
- THEN a span named `transcribe.file` is emitted with `status=ok`
- AND a counter `transcription_requests_total{provider="groq"}` increments by 1

### Requirement: CacheManager for Transcription Results

The system SHOULD cache completed transcription results by audio file
SHA-256 for retrieval on re-runs. Cache hit rate MUST be exposed as a
metric.

#### Scenario: Identical audio re-transcribed

- GIVEN an audio file was transcribed 5 minutes ago
- WHEN the same file is submitted again
- THEN the cached `TranscriptionResult` is returned without provider call
- AND `cache_hits_total` increments by 1

### Requirement: I18nManager Replaces Legacy Localization

The system MUST route all UI strings through the core-cenf `I18nManager`.
The legacy `LocalizationManager` and direct `lang/es.json` reads from
services MUST be removed.

#### Scenario: Locale switch

- GIVEN `I18nManager` is configured with locale `"en_US"`
- WHEN a component requests the key `transcribe.start`
- THEN it receives the English translation
- AND the legacy localization module is not imported
