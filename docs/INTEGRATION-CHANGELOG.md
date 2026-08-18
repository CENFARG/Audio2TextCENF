# Integration Changelog — v0.15.0 → v0.16.0

## Overview

This integration merges Pablo's v0.15.0 fixes and features into Gonzalo's v0.16.0 Clean Architecture. The base is `origin/feature/audio2text-v0.16.0-tauri-migration` with Pablo's improvements ported on top.

---

## Commits

| Hash | Description |
|------|-------------|
| `adbb38c` | fix(tauri): resolve build issues — add tauri-build dep, fix permissions, fix main.rs, add placeholder icons |
| `a26c55c` | feat(backend): port audio chunking and operation tracker to Clean Architecture |
| `c9cbb45` | feat(backend): port hotkey service and vocabulary import/export |
| `822c055` | feat(config): add output_language field for independent language settings |
| `e0d4719` | test(providers): add comprehensive provider tests |
| `18531c7` | test(config): add comprehensive config schema and migration tests |
| `307c72f` | fix(frontend): remove core-cenf-ts dependency temporarily |
| `982a9bf` | feat(tauri): port hotkey parsing and single-instance guard |

---

## What Was Ported

### From Pablo (v0.15.0)

1. **Audio Chunking** (`audio2text/services/audio_chunker.py`)
   - Client-side chunking on silence boundaries (<30s)
   - Prevents Groq seam loss ("tildes que se caen" bug)
   - Invariants: no sample loss, no chunk >30s, cuts at silences

2. **Operation Tracker** (`audio2text/services/operation_tracker.py`)
   - Exactly-once operation state machine
   - Bounded event history (max 256 events)
   - OperationRegistry with automatic cleanup

3. **Hotkey Service** (`audio2text/services/hotkey_service.py`)
   - Hotkey parsing, validation, registration
   - IPC fallback for mouse-button hotkeys
   - Non-fatal registration (warns if already registered)

4. **Vocabulary Import/Export** (`audio2text/services/vocabulary_service.py`)
   - Export with `=` format (user-friendly)
   - Import supports `=`, `→`, and space-separated formats
   - JSON roundtrip support

5. **Language Switch Independence** (`audio2text/config/schema.py`)
   - `output_language` field in AudioConfig
   - Independent of UI language (`localization.language`)

6. **Tauri Shell Improvements** (`src-tauri/src/hotkeys.rs`, `lib.rs`)
   - Hotkey string parsing (Ctrl+Alt+F9 → Tauri modifiers)
   - Single-instance guard (focuses existing window)
   - Non-fatal hotkey registration

### From Gonzalo (v0.16.0) — Base Architecture

1. **Clean Architecture** (`audio2text/`)
   - FastAPI backend with 16 routes + WebSocket
   - 13 services, 4 providers, domain entities
   - Ports & Adapters pattern

2. **Pydantic Config** (`audio2text/config/`)
   - Nested schema with migration from v0.15 flat format
   - XOR key decoder for API keys

3. **Svelte 5 Frontend** (`src/`)
   - 5 views, 6 components, design tokens
   - APIClient with WebSocket support

4. **Provider System** (`audio2text/providers/`)
   - Groq, Faster Whisper, NVIDIA Riva, Mock adapters
   - Factory pattern with fallback chain

---

## Tests

| Category | Count | Status |
|----------|-------|--------|
| New tests (Pablo) | 107 | ✅ All pass |
| Existing tests (Gonzalo) | 351 | ✅ Pass |
| Pre-existing failures | 19 | ⚠️ Known issues |
| Pre-existing errors | 16 | ⚠️ Missing dependencies |
| **Total passing** | **458** | ✅ |

### New Test Files

- `tests/unit/test_audio_chunker.py` — 22 tests
- `tests/unit/test_operation_tracker.py` — 19 tests
- `tests/unit/test_hotkey_service.py` — 11 tests
- `tests/unit/test_vocabulary_import_export.py` — 16 tests
- `tests/unit/test_providers_comprehensive.py` — 17 tests
- `tests/unit/test_config_comprehensive.py` — 22 tests

---

## Known Issues

1. **`core_infrastructure` not installed** — external package from Gonzalo's env, causes 16 infrastructure test errors
2. **`core-cenf-ts` not available** — frontend bootstrap is a no-op placeholder
3. **pnpm install slow** — network issue, requires manual retry
4. **16 legacy test failures** — tests for old `backend/` code that was superseded by `audio2text/` Clean Architecture (pre-existing, not regressions)

---

## Next Steps

1. Get `core_infrastructure` package from Gonzalo and install it
2. Get `core-cenf-ts` frontend package from Gonzalo
3. Complete `pnpm install` and verify frontend build
4. Run full E2E tests with Playwright

---

*Generated 2026-08-18 from `feature/integration-v0.16.0`*
