# Proposal: Tauri v2 UI Replacement

## Intent

Replace the Flet UI (~30 Python files) with Tauri v2 + TypeScript. Flet couples UI
logic to the Python process and bundles a Flutter runtime. The backend is now a
stable FastAPI (16 routes + WebSocket at `127.0.0.1:8765`) with zero coupling to
the Flet layer — a clean UI-only swap. Tauri v2 uses the OS-native WebView, so the
Rust shell stays ~250 lines while all UI logic lives in TypeScript.

## Scope

### In Scope
- Tauri v2 shell: Rust commands for hotkeys, tray, file dialogs, window management
- TypeScript frontend reproducing all 6 views (transcribe, history, settings, info, update, main)
- core-cenf-ts BootstrapOrchestrator (Config, Log, I18n, Cache, HttpClient, ErrorHandling, FeatureFlag, RateLimiter)
- Direct REST/WS consumption of Python backend (no Rust proxy)
- Typed API client generated from FastAPI OpenAPI schema

### Out of Scope
- Python backend changes (contract frozen)
- core-cenf-ts manager implementation (consumed as-is)
- Mobile targets (desktop-first)
- New features beyond current Flet parity

## Capabilities

### New Capabilities
- `tauri-shell`: Rust command layer — global hotkeys, system tray, file dialogs, window lifecycle. IPC boundary between TS and OS.
- `frontend-ui`: TypeScript app — 6 views, components, state management, routing, theming. Full Flet feature reproduction.
- `frontend-infrastructure`: core-cenf-ts BootstrapOrchestrator integration for frontend managers.

### Modified Capabilities
None. Previous specs (`transcription-agents`, `infrastructure-core`, `legacy-elimination`) are all backend concerns untouched by a UI swap.

## Approach

1. `create-tauri-app` scaffolds Rust shell + TS frontend (framework TBD — see questions)
2. Rust `#[tauri::command]` functions for OS access: `register_hotkey`, `set_tray`, `open_dialog`, `set_window` (~250 lines)
3. TS frontend calls backend directly via `fetch` (REST) + `WebSocket` (streaming)
4. core-cenf-ts `BootstrapOrchestrator` initializes frontend managers mirroring Python bootstrap
5. Generate typed API client from `/openapi.json`
6. Delete `audio2text/ui/` after parity verification

```
TS ──REST/WS──> FastAPI (8765)
TS ──Tauri IPC──> Rust ──> OS (hotkeys, tray, dialogs)
```

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `src-tauri/` | New | Rust shell, Cargo.toml, tauri.conf.json |
| `src/` | New | TypeScript frontend |
| `audio2text/ui/` | Removed | Flet UI deleted after parity |
| `audio2text/api/` | Unchanged | Consumed as-is |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Rust toolchain not installed | High | `rustup` is first apply-phase task |
| Tauri learning curve | Medium | Rust surface tiny (~250 lines); TS carries all logic |
| Dual-frontend during migration | Medium | Launcher flag switches UIs until parity proven |
| Streaming parity (WS) | Medium | Port `streaming.py` early as spike |

## Rollback Plan

Flet UI stays untouched until Tauri passes parity verification. Rollback = delete
`src/`, `src-tauri/`, revert `main.py` entry point. No backend changes to revert.

## Dependencies

- Rust toolchain via `rustup` (not yet installed)
- Tauri v2 CLI, core-cenf-ts (19 managers)
- FastAPI OpenAPI schema (already served at `/openapi.json`)

## Success Criteria

- [ ] Tauri app renders all 6 views
- [ ] Global hotkeys (F1-F12) fire via Rust commands
- [ ] System tray responds to clicks
- [ ] Real-time streaming over WebSocket
- [ ] 16 REST endpoints consumed with type safety
- [ ] core-cenf-ts managers bootstrapped
- [ ] `audio2text/ui/` deleted, no regressions
- [ ] Cold start < 2s

## Proposal Question Round

> Interactive mode (A1). These questions shape the spec and design phases. Please answer or skip.

1. **TS framework**: React (ecosystem, shadcn/ui), Svelte 5 (ergonomics, smaller bundle), or SolidJS (fine-grained reactivity)?
2. **State management**: Zustand (simple stores), signals (Svelte/Solid built-in), or core-cenf-ts state if it offers one?
3. **Migration strategy**: parallel (both UIs live behind a flag, gradual parity) or cutover (replace Flet in one step)?
4. **Component library**: shadcn/ui (copy-paste, Tailwind), headless + custom design, or existing theme port from `theme.py`?
