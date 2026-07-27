# Proposal: Audio2Text Tauri v2 UI Migration

## Intent

Replace the Flet-based UI with Tauri v2 + Svelte 5 following CES v0.1.0. The backend (FastAPI, 16 routes, WebSocket at 127.0.0.1:8765) stays untouched — only the presentation layer changes, reducing memory footprint from ~120 MB (Flet) to ~25 MB (Tauri).

## Scope

### In Scope
- Tauri v2 shell with minimal Rust (~250 lines: IPC commands, capabilities, system tray)
- Svelte 5 frontend — 5 views (Transcribe, History, Settings, Info, Update) with Runes ($state, $derived, $effect)
- Design tokens (Pablo's Dark Goldenrod package → `src/design-tokens/`)
- core-cenf-ts infrastructure (19 managers)
- shadcn-svelte components for all 15 existing Flet controls
- Global hotkeys via Tauri plugin + system tray
- Backend API client (HTTP + WebSocket) ported to Svelte

### Out of Scope
- New features or business logic
- Backend changes of any kind
- Multi-tenant variants (GENERAL/CONTRERAS/CUTIGNOLA) — deferred
- Grama/agentic extensions

## Capabilities

### New Capabilities
- `tauri-shell`: Tauri v2 container — Rust command handlers, IPC bridge, `capabilities/default.json`, system tray, global shortcut plugin
- `ces-ui-components`: Svelte 5 views + shadcn-svelte components — AudioCapture, TranscriptionPanel, RecordingOverlay, StatusBar, SettingsPanel, HistoryPanel, EmojiPicker, HotkeyConfig, ProviderConfig, VocabularyEditor, LanguageSelect, ContextBlocksSelector, AIEnhancementTrigger, UpdatePanel, InfoPanel
- `design-tokens-system`: CSS custom properties from Pablo's package, integrated with Tailwind v4 `@theme` directive

### Modified Capabilities
None — backend is unchanged. No spec-level behavior changes to any existing capability.

## Approach

1. `create-tauri-app` with SvelteKit template (pnpm + Turborepo)
2. Copy `design-tokens/` to `src/`, import `tokens.css`, wire `@theme` in Tailwind v4 config
3. Add shadcn-svelte components (bits-ui, lucide-svelte)
4. Port views sequentially: Transcribe (recording + WS streaming) → Settings (~8 sub-panels) → History (search + emoji) → Info → Update
5. Write Rust commands: `toggle_recording`, `get_hotkeys`, `set_hotkey`, `get_audio_devices`, `show_tray`
6. Remove `audio2text/ui/` Flet code at final PR
7. Architecture: SvelteKit ↔ Tauri IPC (native features) + HTTP/WS → FastAPI backend

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `audio2text/ui/` | Removed | Entire Flet layer — 5 views, 15 components, state, theme, client |
| `src-tauri/` | New | Rust backend (Cargo.toml, src/lib.rs, capabilities/, icons/) |
| `src/` | New | Svelte 5 frontend (routes/, lib/components/, lib/stores/) |
| `pnpm-workspace.yaml` | New | Turborepo monorepo workspace |
| `package.json` (root) | New | pnpm workspace root |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Rust toolchain setup friction | Med | CI via tauri-action; document rustup prerequisites |
| Chained PRs > 400 lines | High | Split into 4 slices: (1) shell+tokens, (2) transcribe, (3) settings, (4) history+info+update |
| WebSocket streaming in Tauri | Low | Tauri webview supports WS — same HTTPX approach, port the APIClient |
| shadcn-svelte Svelte 5 compat | Low | Pin to compatible versions; CES mandates this stack |

## Rollback Plan

Flet UI stays accessible in git history on `main`. Revert the feature branch. Zero backend changes → complete rollback safety on the server side.

## Dependencies

- Rust toolchain (rustup, cargo, MSVC build tools on Windows)
- Node 20+ / pnpm 9+
- `core-cenf-ts` package published and installable
- Pablo's design tokens package (already delivered)

## Success Criteria

- [ ] All 5 views render with identical functionality to current Flet app
- [ ] WebSocket streaming transcription works through Tauri webview
- [ ] Global hotkeys trigger correctly via Tauri plugin
- [ ] System tray show/hide functions
- [ ] Dark/Light mode toggle survives app restart
- [ ] All 15 Flet components ported to Svelte 5 (no feature regression)
- [ ] Flet dependency removed from project; Tauri binary build passes

## Proposal Question Round

1. **Chained PR strategy**: ~3000+ line migration. Split into 4 chained PRs (shell+tokens → transcribe → settings → history+info+update) or prefer fewer slices with larger diffs?

2. **core-cenf-ts readiness**: Is core-cenf-ts v0.1.0 published and installable from GitHub, or does this migration need to land concurrently with it?

3. **Flet removal timing**: Remove `audio2text/ui/` in PR #1 (dangling imports, no runtime impact since Flet frontend won't be launched) or only in the final PR after full verification?

4. **Design token variants**: Apply Pablo's Dark Goldenrod tokens as-is for all variants, or reserve space for per-variant (CONTRERAS, CUTIGNOLA) color overrides via CSS variable swapping?

5. **Hotkey implementation**: Tauri global-shortcut plugin (native, no Python dependency) or keep Python's `keyboard` library running as a sidecar process?
