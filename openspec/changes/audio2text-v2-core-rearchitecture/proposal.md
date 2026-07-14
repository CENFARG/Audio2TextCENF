# Proposal: Audio2Text v2 Core Rearchitecture

## Intent

Eliminate the dual-maintenance burden between legacy `backend/` (~3,000 lines), `ui/` (CustomTkinter), `ui_flet/` (abandoned), and the clean `audio2text/` package. Adopt core-cenf-py for all cross-cutting infrastructure. Refactor transcription/metadata/post-processing agents to Adapter+Provider (depend on Protocols, inject Adapters).

## Scope

### In Scope
- Delete `backend/`, `ui/`, `ui_flet/` (git history only)
- Install `core-cenf-py@v0.1.0`; wire via `BootstrapOrchestrator`
- Replace config/logging/secrets/errors/cache with managers M01–M04, M07
- Refactor transcription/metadata/post-processing to Adapter+Provider
- Migrate XOR API-key obfuscation → `SecretManager` (M03)

### Out of Scope
- UI replacement (Tauri v2 = separate change)
- New features, REST API versioning, contract-breaking changes

## Capabilities

> `openspec/specs/` is empty — all capabilities are NEW.

### New Capabilities
- `infrastructure-core`: core-cenf integration (config, logging, secrets, errors) via BootstrapOrchestrator
- `transcription-agents`: Adapter+Provider for transcription, metadata, post-processing
- `legacy-elimination`: removal of `backend/`, `ui/`, `ui_flet/` + config migration

### Modified Capabilities
- None

## Approach

1. **Prerequisite (RESOLVED)**: `audio2text/` merged from `mvp-integration` (95 files, 11,995 lines). Tests merged (24 files, 3,738 lines).
2. Install `core-cenf-py@v0.1.0`; create `audio2text/infrastructure/bootstrap.py` wiring 18 managers.
3. Define ports in `audio2text/providers/` → `TranscriptionProvider`, `MetadataProvider`, `PostProcessingProvider` (injectable adapters).
4. Refactor services to depend on Protocols, inject core-cenf managers.
5. Delete legacy `backend/`, `ui/`, `ui_flet/`, `main.py`, `verification_test.py` in **chained PRs** (one directory per slice, ≤400 lines).
6. Update CI/CD (`.github/workflows/ci.yml`) to target `audio2text/` and `tests/` paths.
7. TDD per slice: RED-GREEN-REFACTOR with work-unit-commits.

## Affected Areas

| Area | Impact |
|------|--------|
| `backend/`, `ui/`, `ui_flet/` | Removed |
| `audio2text/config/` | Modified — ConfigManager adapter |
| `audio2text/providers/` | Modified — Adapter+Provider |
| `audio2text/services/` | Modified — inject managers |
| `audio2text/infrastructure/` | New — bootstrap + wiring |
| `main.py`, `requirements.txt` | Modified |

## Risks

| Risk | L | Mitigation |
|------|---|------------|
| ~~`audio2text/` absent on branch~~ | — | RESOLVED: merged 95 files + 24 tests |
| External consumers confirmed (38 imports) | Low | All within deletion scope (ui/, ui_flet/, tests/) |
| Breaking 17 unit + 3 E2E tests | Med | TDD per slice; full suite per PR |
| Config migration JSON+XOR → SecretManager | Med | Migration script + golden test |
| Review budget exceeded | High | Chained PRs (C3), ≤400 lines each |
| core-cenf-py dependency availability | Low | Already installed in user environment |
| 18-manager wiring complexity | Med | Incremental: wire 3-4 managers per slice |

## Rollback Plan

- Each chained PR independently revertible; legacy persists in git history.
- Keep legacy `config.json` reader as fallback during transition.

## Dependencies

- `core-cenf-py@v0.1.0`, Python 3.12.10
- Merge of `audio2text/` package (hard prerequisite)

## Success Criteria

- [ ] `audio2text/` is sole codebase; zero legacy imports
- [ ] core-cenf managers wired via `BootstrapOrchestrator`
- [ ] Adapter+Provider for transcription/metadata/post-processing
- [ ] All tests pass; coverage ≥ 50%
- [ ] Each PR ≤ 400 changed lines; CI green

## Proposal Question Round → RESOLVED

> Answers from user (2026-07-14). Applied to scope and approach.

1. **Config migration**: ✅ Auto-migrate from legacy `config.json` (incl. XOR keys). Migration script + golden test.
2. **Provider support**: ✅ All three (Groq, faster-whisper, NVIDIA Riva) survive v2. All refactored to Adapter+Provider.
3. **Block system**: ✅ Refactor TaskExtractor/Summary/KeywordExtractor as injectable adapters (not pipeline stages).
4. **Hotkey ownership**: ✅ Wrap in core-cenf manager (M13 DependencyManager for dynamic resolution, M22 StateMachineManager for recording FSM). No risk, helps standardization.
5. **External consumers**: ✅ VERIFIED. 38 direct `from backend` imports across 13 files (ui/, ui_flet/, tests/, main.py) + 23 mock patches. All consumers are within deletion scope. Safe to proceed.

## core-cenf Integration Analysis

**core-cenf-py (22 managers)** — analyzed from `C:\Dropbox\DOC.RECA\06-Software\core-cenf-py\AGENTS.md`:

| Manager | Audio2Text Use |
|---------|---------------|
| M01 ConfigManager | Replace legacy ConfigManager (XOR) |
| M02 LoggerManager | Structured logging |
| M03 SecretManager | API keys instead of XOR |
| M04 ErrorHandlingManager | @handle_errors decorator |
| M05 ObservabilityManager | RED metrics + tracing |
| M06 AuthManager | JWT for API routes |
| M07 CacheManager | Cache transcription results |
| M08 DatabaseManager | History/metadata storage |
| M09 FileStorageManager | Audio file storage |
| M10 TaskQueueManager | Async transcription jobs |
| M11 ExternalAPIManager | Groq API with circuit breaker |
| M12 FeatureFlagManager | Toggle providers/blocks |
| M13 DependencyManager | Dynamic provider resolution |
| M16 RateLimiterManager | API rate limiting |
| M17 I18nManager | Multi-language (es/en) |
| M20 UpdateManager | GitHub auto-update |
| M21 BusEventManager | Decoupled component pub/sub |
| M22 StateMachineManager | Recording/transcription FSM |

**core-cenf-ts (19 managers)** — reserved for future Tauri v2 frontend change. Not in scope here.
