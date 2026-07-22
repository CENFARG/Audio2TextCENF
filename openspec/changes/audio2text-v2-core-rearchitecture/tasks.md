# Tasks: Audio2Text v2 Core Rearchitecture

> **Change**: `audio2text-v2-core-rearchitecture`
> **Branch**: `feature/audio2text-v2-core-rearchitecture`
> **Delivery**: Feature Branch Chain (13 chained PRs, tracker draft, no-merge)
> **Package import**: `core_infrastructure` (golden rule: only `infrastructure/` may import it)

---

## Review Workload Forecast

| Metric | Value |
|---|---|
| Total chained PRs | 13 |
| Total est. lines | ~4,730 |
| Per-PR ceiling | 400 additions + deletions |
| Slices near ceiling (4, 6, 9) | Must split or sub-extract if apply exceeds |
| Verification gate per slice | `pytest tests/` green |
| Legacy import guard (slice 11+) | `rg "from (backend\|ui\|ui_flet)\." audio2text/` clean |
| Coverage gate (final slice) | `pytest --cov=audio2text --cov-fail-under=50` |

```
Decision needed before apply: No
Chained PRs recommended: Yes
Chain strategy: feature-branch-chain
400-line budget risk: High
```

---

## Suggested Work Units

| Unit | Goal | Base Branch | Est. Lines |
|---|---|---|---|
| 1 | bootstrap skeleton + ConfigManager + LoggerManager | `feature/audio2text-v2-core-rearchitecture` | ~360 |
| 2 | SecretManager + ErrorHandlingManager + XOR migration harden | `slice-1-bootstrap-config-logger` | ~380 |
| 3 | Observability + Cache + I18n managers + replace LocalizationManager | `slice-2-secret-errors` | ~370 |
| 4 | TranscriptionProvider ports + refactor 3 adapters + delete `base.py` | `slice-3-observability-cache-i18n` | ~390 |
| 5 | DependencyManager + fallback chain + factory delegation | `slice-4-provider-ports` | ~340 |
| 6 | PostProcessingBlock port + 3 block adapters + ExternalAPIManager | `slice-5-dependency-factory` | ~390 |
| 7 | MetadataProvider port + JSONL adapter + in-memory test | `slice-6-blocks-external-api` | ~300 |
| 8 | BusEventManager + StateMachineManager recording FSM | `slice-7-metadata-port` | ~360 |
| 9 | TranscriptionService inject all managers + `@handle_errors` + refactor `api/dependencies.py` | `slice-8-events-fsm` | ~400 |
| 10 | remaining managers (Auth, DB, FileStorage, TaskQueue, FeatureFlag, RateLimiter, Update) | `slice-9-service-inject` | ~380 |
| 11 | delete `backend/` directory + fix straggler imports | `slice-10-remaining-managers` | ~350 |
| 12 | delete `ui/`, `ui_flet/`, root `main.py`, `verification_test.py` | `slice-11-delete-backend` | ~390 |
| 13 | CI/CD + `pyproject.toml` + `setup.py` + `scripts/build.py` target `audio2text/` | `slice-12-delete-ui-entries` | ~360 |

Tracker: `feature/audio2text-v2-core-rearchitecture → main` (draft PR, no-merge). Child #1 targets tracker; children #2..#13 target the previous child's branch.

---

## Phase 1 — Infrastructure Core (slices 1-4)

- [x] 1.1 **RED** — Create `tests/infrastructure/test_bootstrap_order.py` asserting M01→M02→M03→M04→M05 instantiation order from spec scenario "Bootstrap initializes all managers in order".
- [x] 1.2 **GREEN** — Create `audio2text/infrastructure/__init__.py` exporting `get_registry()`; create `audio2text/infrastructure/bootstrap.py` with `BootstrapOrchestrator` wiring ConfigManager + LoggerManager in spec order; halt on `ConfigError`.
- [x] 1.3 Create `audio2text/infrastructure/registry.py` (`ManagerRegistry` typed accessors) and `audio2text/infrastructure/ports.py` (re-exported `core_infrastructure` Protocols); single import site for `core_infrastructure`.
- [x] 1.4 **RED** — Add `test_bootstrap_halts_on_config_failure`: missing `config.toml` raises `ConfigError` before manager #2; assert no half-init state (spec scenario "Bootstrap halts on config failure").
- [x] 1.5 **GREEN** — Add ConfigError halt guard in `bootstrap.py`; refactor halting path; tests pass.
- [x] 2.1 Create adapters: secret_adapter, config_adapter, logger_adapter wrapping core_infrastructure managers
- [x] 2.2 Adapter tests with fake keyring fixture
- [x] 2.3 **RED** — `tests/config/test_migration_idempotent.py`: golden `config.json` with XOR+Base64 `groq_api_key`; assert SecretManager receives plaintext; idempotent re-run guard
- [x] 2.4 **GREEN** — idempotent backup guard in migration.py; `set_secret()` API match; golden test fixture `tests/fixtures/config_v015.json`
- [x] 3.1 Wire ObservabilityManager (M05) with NoopObservabilityAdapter; emit increment_counter
- [x] 3.2 Wire CacheManager (M07) with MemoryCacheAdapter; cache by key, get_or_set with factory
- [x] 3.3 Wire I18nManager (M17) with InMemoryI18nAdapter; locale-first translation format
- [x] 4.1 Create ports/transcription_provider.py with @runtime_checkable Protocol
- [x] 4.2 Create adapters/ with groq_adapter, faster_whisper_adapter, nvidia_riva_adapter, mock_adapter; fix cenf_core→core_infrastructure
- [x] 4.3 base.py → compatibility shim; update factory.py paths; add protocol tests (tests/unit/test_protocols.py)

---

## Phase 2 — Adapter+Provider Agents (slices 5-9)

- [ ] 5.1 **RED** — `tests/providers/test_factory.py`: assert `DependencyManager` resolves `groq`, `faster_whisper`, `nvidia`; unknown type raises `ValueError` listing valid types (spec scenario "Unknown provider type rejected").
- [ ] 5.2 **GREEN** — Wire `DependencyManager` (M13) in `bootstrap.py`; register 3 adapters under their type keys; add `get_provider(type)` and `resolve_fallback_chain(config)` helpers.
- [ ] 5.3 Modify `audio2text/providers/factory.py` to delegate to `DependencyManager`; keep as thin deprecated facade (Q4 default) — add `DeprecationWarning`.
- [ ] 6.1 Create `audio2text/providers/ports/post_processing_provider.py` with `PostProcessingBlock` Protocol (`process(text) -> BlockResult`).
- [ ] 6.2 Create `adapters/task_extractor_adapter.py`, `adapters/summary_adapter.py`, `adapters/keyword_extractor_adapter.py` (moved from `audio2text/blocks/`, Protocol-conformant).
- [ ] 6.3 Wire `ExternalAPIManager` (M11) in `bootstrap.py`; all LLM calls route through it (spec REQ "Post-Processing via ExternalAPIManager").
- [ ] 6.4 **RED** — `tests/providers/test_circuit_breaker.py`: 5 consecutive LLM failures → `CircuitOpenError` → block returns fallback text (spec scenario "Circuit breaker trips on Groq LLM failure").
- [ ] 7.1 Create `audio2text/providers/ports/metadata_provider.py` with `MetadataProvider` Protocol (`save`, `list`, `get`).
- [ ] 7.2 Create `audio2text/providers/adapters/jsonl_metadata_adapter.py` (default adapter, moves logic from `audio2text/services/metadata_service.py`).
- [ ] 7.3 **RED** — `tests/providers/test_metadata_port.py`: inject in-memory adapter; assert no file on disk; metadata is written to adapter only (spec scenario "Custom MetadataProvider injected").
- [ ] 8.1 Wire `BusEventManager` (M21) in `bootstrap.py`; publish `transcription.started`, `transcription.completed`, `transcription.failed` from `TranscriptionService`.
- [ ] 8.2 Wire `StateMachineManager` (M22) for recording FSM: states `idle → recording → transcribing → done`, terminal `error`; only valid transitions allowed (spec REQ "StateMachineManager for Recording FSM").
- [ ] 8.3 **RED** — `tests/services/test_fsm.py`: happy-path (`idle→recording→transcribing→done`) passes; double-`start` from `recording` raises `InvalidTransition` and state stays `recording` (spec scenarios 1+2).
- [ ] 9.1 **RED** — `tests/services/test_transcription_service_integration.py`: service composed of MockProvider + 2 injected blocks + in-memory MetadataProvider + captured bus events; assert event sequence + result text.
- [ ] 9.2 **GREEN** — Rewrite `audio2text/services/transcription_service.py`: inject provider, blocks list, metadata port, bus, fsm; wrap public methods with `@handle_errors` from `ErrorHandlingManager` (spec scenario "Service method raises").
- [ ] 9.3 **RED** — `tests/api/test_dependencies_registry.py`: `api/dependencies.py` reads via `registry.get_config()`, `registry.get_secret()`, etc. — no direct `core_infrastructure` import in `audio2text/api/`.
- [ ] 9.4 **GREEN** — Modify `audio2text/api/dependencies.py`: remove singleton cache + direct `core_infrastructure` imports; replace with `registry.get_*()` accessors. Modify `audio2text/api/app.py` to accept `ManagerRegistry` in lifespan. Modify `audio2text/api/routes/*.py` to read via registry.

---

## Phase 3 — Legacy Elimination (slices 10-13)

- [ ] 10.1 Wire `AuthManager` (M06), `DatabaseManager` (M08), `FileStorageManager` (M09), `TaskQueueManager` (M10), `FeatureFlagManager` (M12), `RateLimiterManager` (M16), `UpdateManager` (M20) into `bootstrap.py`; typed accessors in `registry.py`; smoke tests `tests/infrastructure/test_remaining_managers.py`.
- [ ] 10.2 Modify `audio2text/main.py` to call `BootstrapOrchestrator().bootstrap()` before launching FastAPI app + Flet UI.
- [ ] 11.1 Run `rg "from backend\." audio2text/ tests/`; identify straggler imports; fix in this slice.
- [ ] 11.2 Delete `backend/` directory; rerun `rg` → 0 matches; `pytest tests/` green (spec scenarios "All legacy directories gone" + "Legacy preserved in git history").
- [ ] 12.1 Run `rg "from (ui|ui_flet)\." audio2text/ tests/`; fix stragglers; delete `ui/`, `ui_flet/`, root `main.py`, `verification_test.py`; suite green.
- [ ] 12.2 Verify `git log --oneline -- backend/config_manager.py` still shows historical commits reachable.
- [ ] 13.1 Modify `.github/workflows/ci.yml`: target `audio2text/` + `tests/`; remove `backend/`, `ui/`, `ui_flet/` path triggers; bump Python to 3.12 (spec REQ "CI/CD Path Update").
- [ ] 13.2 Modify `pyproject.toml`: `[tool.setuptools.packages.find]` → `include = ["audio2text*"]` only; add `core_infrastructure` dep; remove legacy entry points (spec REQ "pyproject.toml and setup.py Cleanup").
- [ ] 13.3 Modify `setup.py`: sole package `audio2text`; entry `audio2text.main:main`. Modify `scripts/build.py`: PyInstaller targets `audio2text/`, no `backend/`/`ui/` references (spec REQ "Build Script Cleanup").

---

## Phase 4 — Verification & Cleanup (cross-cutting)

- [ ] 4.1 **Tracker PR** — Open draft PR `feature/audio2text-v2-core-rearchitecture → main` (no-merge); populate with dependency diagram from design §5; add chain context block.
- [ ] 4.2 **Per-slice PR body** — Each child PR must include: chain context (start, end, depends-on, follow-up, out-of-scope), `📍` marker, `additions + deletions ≤ 400` evidence (`gh pr view --json additions,deletions`).
- [ ] 4.3 **Per-slice gate** — Each PR runs: `pytest tests/ -q` (green), `pytest --cov=audio2text --cov-fail-under=50` (only final slice), and (from slice 11) `rg "from (backend|ui|ui_flet)\." audio2text/ --count` = 0.
- [ ] 4.4 **Independence test** — Revert any merged slice on a throwaway branch; assert remaining tree still compiles and `pytest tests/` green (spec scenario "Independently revertible slices").
- [ ] 4.5 **Coverage final** — After slice 13: `pytest --cov=audio2text --cov-report=term-missing`; confirm ≥50%; archive change via `sdd-archive`.

---

## Out-of-Scope (explicit)

- Tauri v2 UI replacement (separate change)
- New features, REST API versioning, contract-breaking changes
- core-cenf-ts frontend managers (reserved for Tauri change)

## References

- Design: `openspec/changes/audio2text-v2-core-rearchitecture/design.md`
- Specs: `openspec/changes/audio2text-v2-core-rearchitecture/specs/{infrastructure-core,transcription-agents,legacy-elimination}/spec.md`
- Proposal: `openspec/changes/audio2text-v2-core-rearchitecture/proposal.md`
- Skills: `chained-pr`, `work-unit-commits`
