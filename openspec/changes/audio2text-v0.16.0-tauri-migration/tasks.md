# Tasks: Audio2Text — Tauri v2 UI Migration (v0.16.0)

> **Change**: `audio2text-v0.16.0-tauri-migration`
> **Branch**: `feature/audio2text-v0.16.0-tauri-migration`
> **Delivery**: 5 chained PRs on tracker branch, ≤400 lines each

---

## Review Workload Forecast

| Metric | Value |
|---|---|
| Total chained PRs | 5 |
| Total est. lines | ~1,800 |
| Per-PR ceiling | 400 |

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
| 1 | Tauri shell + SvelteKit + tokens + core-cenf-ts | tracker | ~350 |
| 2 | TranscribeView + WS streaming + recording overlay | PR #1 | ~380 |
| 3 | SettingsView — 8 panels | PR #2 | ~380 |
| 4 | History + Info + Update views | PR #3 | ~350 |
| 5 | Polish + Playwright E2E + CI/CD + delete Flet | PR #4 | ~350 |

---

## Phase 1 — Tauri Shell + Foundation (Slice 1, ~350 lines)

- [x] 1.1 Scaffold Tauri v2 — Cargo.toml, src-tauri/src/lib.rs, src-tauri/src/main.rs
- [x] 1.2 Configure `src-tauri/Cargo.toml`: tauri v2, serde, serde_json, tauri-plugin-shell, tauri-plugin-global-shortcut
- [x] 1.3 Configure tauri.conf.json`: window 1100x760, identifier `com.cenf.audio2text`, `bundle.externalBin`
- [x] 1.4 Configure capabilities/default.json`: scoped `shell:allow-execute`, `plugin:global-shortcut`, `window:allow-*`
- [x] 1.5 Implement src-tauri/src/lib.rs`: commands `start_backend`, `stop_backend`, `get_backend_status`, `toggle_recording`, `get_hotkeys`, `set_hotkey`, `show_tray` (~400 lines)
- [x] 1.6 Copy Pablo's `design-tokens/tokens.json` + `tokens.css` to `src/design-tokens/`
- [ ] 1.7 Create `src/app.css` with Tailwind v4 `@theme` referencing `--dt-*` CSS vars
- [x] 1.8 Wire core-cenf-ts `BootstrapOrchestrator` in `src/lib/infrastructure/bootstrap.ts`
- [x] 1.9 Create src/app.svelte` root component + `Navigation.svelte` with 5 tabs + LanguageSelect
- [x] 1.10 Configure pnpm-workspace, svelte, vite, tailwind, tsconfig-workspace.yaml`, `turbo.json`, `svelte.config.js`, `vite.config.ts`, `tailwind.config.ts`, `tsconfig.json`, `components.json`

## Phase 2 — Transcription Core (Slice 2, ~380 lines)

- [ ] 2.1 **RED** — Test `APIClient` HTTP methods + Zod schema validation
- [ ] 2.2 **GREEN** — Create `src/lib/infrastructure/api-client.ts` (16 endpoints + WS, typed)
- [ ] 2.3 Create `src/lib/infrastructure/ws-reconnect.ts` (exponential backoff, max 3 retries)
- [ ] 2.4 Create `src/lib/infrastructure/mock-api-client.ts` (Zod-compatible stub)
- [ ] 2.5 **RED** — Test `$state` runes: transcriptionText, recordingStatus
- [ ] 2.6 **GREEN** — Create `src/lib/state/transcription.svelte.ts`
- [ ] 2.7 Create `AudioCapture.svelte` (record button, shadcn Button) + `RecordingOverlay.svelte` (LED + timer)
- [ ] 2.8 Create `TranscriptionPanel.svelte` (live scroll) + `StatusBar.svelte` + `ContextBlocksSelector.svelte`
- [ ] 2.9 Create `TranscribeView.svelte` composing all components + WebSocket streaming flow
- [ ] 2.10 Create `src/lib/state/hotkey.svelte.ts` + hotkey event listener

## Phase 3 — Settings (Slice 3, ~380 lines)

- [ ] 3.1 **RED** — Test `$state` runes: settings debounced PUT
- [ ] 3.2 **GREEN** — Create `src/lib/state/settings.svelte.ts` (400ms debounce, auto-save)
- [ ] 3.3 Create `ProviderConfig.svelte` (API keys, model dropdowns, FW config)
- [ ] 3.4 Create `HotkeyConfig.svelte` (rebinding UI)
- [ ] 3.5 Create `VocabularyEditor.svelte` (custom corrections CRUD)
- [ ] 3.6 Create remaining settings panels: Audio, Recording, UI, Post-processing, Blocks
- [ ] 3.7 Create `SettingsView.svelte` composing 8 panels + I18nManager for localization
- [ ] 3.8 Test: auto-save on toggle, debounce timing

## Phase 4 — History + Info + Update (Slice 4, ~350 lines)

- [ ] 4.1 Create `HistorySearch.svelte` (searchable list) + `EmojiPicker.svelte`
- [ ] 4.2 Create `HistoryView.svelte` (split layout, CRUD, emoji assign)
- [ ] 4.3 Create `InfoView.svelte` (version, credits, license, system info)
- [ ] 4.4 Create `UpdateView.svelte` (check, download progress, status)
- [ ] 4.5 Create `src/lib/state/navigation.svelte.ts` (current view routing)
- [ ] 4.6 Wire all views into `App.svelte` with Navigation tab switching
- [ ] 4.7 Test: view switching, history search + emoji assign, update check

## Phase 5 — Polish + Cleanup (Slice 5, ~350 lines)

- [ ] 5.1 Write Playwright E2E: full transcription flow (record → stream → stop)
- [ ] 5.2 Write Playwright E2E: settings save/load, history CRUD
- [ ] 5.3 Write Playwright E2E: hotkey trigger + system tray quit
- [ ] 5.4 Configure `.github/workflows/tauri-ci.yml` (tauri-action + Playwright)
- [ ] 5.5 Write Rust `cargo test`: backend start/stop, get_backend_status
- [ ] 5.6 Delete `audio2text/ui/` (entire Flet layer)
- [ ] 5.7 Modify `audio2text/main.py`: remove Flet import, keep sidecar-compatible entry
- [ ] 5.8 Update `audio2text/api/lifespan.py` for sidecar lifecycle
- [ ] 5.9 Run full test suite: Vitest + Playwright + cargo test + pytest — all green
- [ ] 5.10 Update `pyproject.toml`, `setup.py`, docs

## Out of Scope

- Grama features (corrección 1:2:, Engram, Git versioning) — separate change
- Light mode theme tokens (v0.16.1)
- core-cenf-tenant (separate project)
