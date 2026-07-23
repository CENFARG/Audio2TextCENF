# Tasks: Audio2Text v2 Core Rearchitecture

> **Change**: `audio2text-v2-core-rearchitecture`
> **Status**: COMPLETE — 62 tests, 18/18 managers wired, legacy eliminated

---

## Phase 1 — Infrastructure Core (slices 1-4) ✅

- [x] 1.1 Bootstrap skeleton: ConfigManager (M01) + LoggerManager (M02) wiring
- [x] 1.2 ManagerRegistry typed accessors + ports.py Protocol re-exports
- [x] 1.3 ConfigError halt guard (no half-init state)
- [x] 2.1 SecretManager (M03) + ErrorHandlingManager (M04) wiring
- [x] 2.2 XOR config migration: idempotent backup guard + SecretManager integration
- [x] 2.3 Golden test fixture config_v015.json + migration idempotency tests
- [x] 3.1 ObservabilityManager (M05) + CacheManager (M07) + I18nManager (M17) wiring
- [x] 4.1 TranscriptionProvider Protocol (ports/) — replaces ABC base.py
- [x] 4.2 4 adapters: groq_adapter, faster_whisper_adapter, nvidia_riva_adapter, mock_adapter
- [x] 4.3 Fix cenf_core → core_infrastructure in groq + nvidia adapters
- [x] 4.4 base.py → compatibility shim; factory.py updated to adapter paths

## Phase 2 — Adapter+Provider Agents (slices 5-8) ✅

- [x] 5.1 DependencyManager (M13) wired with 4 provider adapter registrations
- [x] 6.1 PostProcessingBlock Protocol port + ExternalAPIManager (M11) wired
- [x] 7.1 MetadataProvider Protocol port
- [x] 8.1 BusEventManager (M21) + StateMachineManager (M22) wired

## Phase 3 — Remaining Managers (slice 10) ✅

- [x] 10.1 AuthManager (M06), DatabaseManager (M08), FileStorageManager (M09) wired
- [x] 10.2 TaskQueueManager (M10), FeatureFlagManager (M12) wired
- [x] 10.3 RateLimiterManager (M16), UpdateManager (M20) wired
- [x] 10.4 All 18 managers bootstrapped in dependency order with typed registry accessors

## Phase 4 — Integration (slice 9) ✅

- [x] 9.1 api/dependencies.py refactored: singletons → ManagerRegistry
- [x] 9.2 cenf_core imports eliminated (was breaking imports)
- [x] 9.3 api/lifespan.py bootstraps registry on startup
- [x] 9.4 TranscriptionService import fixed (ports, not base)

## Phase 5 — Legacy Elimination (slices 11-13) ✅

- [x] 11.1 Delete backend/ directory (source files + cache)
- [x] 12.1 Delete ui/, ui_flet/, main.py, verification_test.py
- [x] 13.1 CI/CD updated to target audio2text/ + Python 3.12
- [x] 13.2 pyproject.toml updated

## Phase 6 — Verification ✅

- [x] 6.1 Smoke integration: bootstrap + domain models + providers coexist
- [x] 6.2 All 7 manager groups functionally exercised
- [x] 6.3 Migration end-to-end: XOR decode → SecretManager → clean output
- [x] 6.4 Protocol tests: duck-typing, factory compatibility
- [x] 6.5 62 tests, all passing

## Deferred (separate changes)

- Block adapter migration (TaskExtractor/Summary/KeywordExtractor) — UI change
- TranscriptionService full injection (@handle_errors, bus events) — UI change
- Chained PRs + tracker — optional, single branch approach used
- FSM transition tests — UI change

## Out of Scope

- Tauri v2 UI replacement (separate change)
- core-cenf-ts integration (separate change)
