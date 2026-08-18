# Changelog — Audio2Text Tauri v2

Todos los cambios de la migración a Tauri v2 + Svelte 5.

Formato basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.0.0/).

---

## [2.0.0] - 2026-08-17

### 🎯 BREAKING CHANGES

- **UI Framework**: Flet UI reemplazada por Tauri v2 + Svelte 5
  - El ejecutable ahora es un binario nativo (~13 MB) en vez de un bundler Python
  - La UI se renderiza en WebView2 (Windows) nativo
  - `ui_flet/` eliminado del proyecto
- **Launch method**: `python main.py` sigue funcionando (legacy). El nuevo método es `pnpm tauri dev` o ejecutar el `.exe`
- **Dependencies**: Se requiere Node.js + pnpm para desarrollo del frontend. El runtime de usuario final no necesita Node.js.

### ✅ Agregado

**Backend Rust (`src-tauri/`):**
- `commands.rs` — Tauri IPC handlers: `start_recording`, `stop_recording`, `get_config`, `save_config`, `get_history`, `auto_paste`
- `sidecar.rs` — Sidecar process manager with JSON-line IPC, health check loop (5s interval), exponential backoff crash recovery (1s→2s→4s→8s→32s max)
- `hotkeys.rs` — Global hotkey registration via `tauri-plugin-global-shortcut`. Default: Ctrl+Alt+F9 toggle recording. Supports custom hotkey strings with modifier parsing (Ctrl, Alt, Shift, Super) and F1-F24, letters, digits, special keys
- `tray.rs` — System tray with Start/Stop Recording, Show/Hide Window, and Quit menu items. Left-click toggles window visibility
- `overlay.rs` — Always-on-top overlay window (220×52px, decorations off) showing recording timer in MM:SS format
- `clipboard.rs` — Auto-paste: copies text to clipboard via `arboard` and simulates Ctrl+V via `enigo`
- `lib.rs` — App setup: plugin init, sidecar spawn, health check, overlay creation, hotkey registration, tray creation, event listeners for recording:started/stopped

**Frontend Svelte 5 (`src/`):**
- `main.ts` — Svelte 5 entry point using `mount()` (not `new App()`)
- `App.svelte` — Root component with tab navigation (Recording, History, Settings)
- `components/RecordingPanel.svelte` — Recording controls and transcription display
- `components/History.svelte` — Transcription history list
- `components/Settings.svelte` — Configuration panel
- `components/StatusBar.svelte` — Connection status indicator
- `components/LanguageSwitch.svelte` — Language selector (es/en)
- `lib/commands.ts` — Typed IPC wrappers for all Tauri invoke calls
- `lib/types.ts` — Full TypeScript type definitions for commands, events, and responses
- `lib/i18n.ts` — Internationalization (es/en)
- `lib/stores/` — Svelte stores for state management

**Python Sidecar (`backend/sidecar_entry.py`):**
- JSON-line server on stdin/stdout
- Command handlers: `start_recording`, `stop_recording`, `get_config`, `save_config`, `get_history`, `register_hotkey`
- Importable as module AND runnable as script

**Configuration:**
- `src-tauri/tauri.conf.json` — Tauri v2 config: CSP with `'self'` on every directive, 800×600 window, shell plugin enabled
- `src-tauri/capabilities/default.json` — Permissions: core, shell, global-shortcut, clipboard-manager
- `vite.config.ts` — Vite 6 + Svelte 5, modulePreload disabled, crossorigin removal plugin
- `svelte.config.js` — Svelte preprocessor config
- `tsconfig.json` — TypeScript strict config
- `pnpm-workspace.yaml` — esbuild allowed for native deps

**Documentation:**
- `docs/ipc-contracts.md` — Complete IPC contract reference with examples
- `docs/sidecar-lifecycle.md` — Sidecar spawn, health check, crash recovery, shutdown
- `CHANGELOG-Tauri.md` — This file

### 🔧 Cambiado

- `package.json` — Version bumped to 2.0.0, added Tauri CLI and plugins
- `Cargo.toml` — audio2text-tauri v2.0.0, edition 2024, added tauri-plugin-shell, global-shortcut, clipboard-manager, arboard, enigo
- `config.json` — `app_version` remains 0.15.0 (backend version independent of UI framework)

### 🗑️ Deprecado

- `ui_flet/` — Eliminado. Tauri v2 reemplaza completamente la UI Flet
- `main.py` — Legacy entry point. Sigue funcionando pero se recomienda usar `pnpm tauri dev` o el ejecutable `.exe`

### 🐛 Corregido

- CSP screens negra: cada directiva CSP ahora tiene `'self'` explícito
- Svelte 5 mount: usa `mount()` en vez de `new App()` para evitar `effect_orphan`
- Vite crossorigin: `modulePreload: false` + plugin remove-crossorigin elimina pantalla blanca en producción
- Hotkey config: shortcuts se registran desde Rust (no desde JSON), evitando `invalid type: map, expected unit`

### 📦 Distribución

- **Ejecutable**: `src-tauri/target/release/Audio2Text.exe` (~13 MB)
- **MSI installer**: `src-tauri/target/release/bundle/msi/*.msi` (~5 MB)
- **Legacy**: `python main.py` sigue funcionando para usuarios existentes

### 📝 Documentación

- `docs/ipc-contracts.md` — Reference completa de IPC commands y events
- `docs/sidecar-lifecycle.md` — Diagrama de estado, spawn, health check, crash recovery
- `CHANGELOG-Tauri.md` — Este archivo

---

## Coexistencia: Legacy (Python) vs Nuevo (Tauri)

Ambas versiones pueden correr en paralelo sin conflictos:

### Legacy (Python + CustomTkinter)
```bash
# Desde la raíz del proyecto
python main.py
```
- UI: CustomTkinter
- Transcripción: Python nativo
- Config: `config.json` (mismo archivo)
- Audio: `./audio/`
- Transcriptions: `./transcriptions/`

### Nuevo (Tauri v2 + Svelte 5)
```bash
# Desarrollo
pnpm install
pnpm tauri dev

# Build producción
pnpm tauri build
# → src-tauri/target/release/Audio2Text.exe
```
- UI: Tauri WebView2 + Svelte 5
- Transcripción: Python sidecar (mismo `backend/`)
- Config: `config.json` (mismo archivo)
- Audio: `./audio/`
- Transcriptions: `./transcriptions/`

### Puntos en Común

| Recurso     | Legacy        | Tauri          | Compartido |
|-------------|---------------|----------------|------------|
| Config      | `config.json` | `config.json`  | Sí         |
| Audio files | `./audio/`    | `./audio/`     | Sí         |
| Transcriptions | `./transcriptions/` | `./transcriptions/` | Sí |
| Backend     | `backend/`    | `backend/` (sidecar) | Sí (sidecar) |
| UI code     | `ui/`         | `src/`         | No         |
| Hotkeys     | Python keyboard | Rust global-shortcut | No |

> **Nota**: No se recomienda ejecutar ambos al mismo tiempo si están grabando audio simultáneamente, ya que competirían por el micrófono.

---

## Rollback Procedure

Si necesitás volver a la versión anterior después de un cambio:

### Rollback completo a legacy
```bash
# Revertir todos los cambios de la migración Tauri
git log --oneline  # Identificar el commit anterior a la migración
git revert <commit-hash>  # Revertir un commit específico

# O revertir todo el rango de la migración
git revert <primer-commit-migracion>..<ultimo-commit-migracion>
```

### Rollback de un cambio específico
```bash
# Ver qué cambió un commit
git show <commit-hash>

# Revertir solo ese commit
git revert <commit-hash>
```

### Rollback a versión exacta
```bash
# Listar tags
git tag -l

# Crear branch desde un tag
git checkout -b rollback-v0.15.0 v0.15.0
```

### Verificar rollback
```bash
# Legacy debe seguir funcionando
python main.py

# Si querés restaurar Tauri después del rollback
git checkout main
pnpm install
pnpm tauri dev
```

---

## What's New (Resumen)

| Feature | Descripción |
|---------|-------------|
| **Native hotkeys** | Ctrl+Alt+F9 global toggle, registrado en Rust (funciona incluso sin foco de ventana) |
| **System tray** | Icono en la bandeja con menú: Start/Stop, Show/Hide, Quit. Click izquierdo toggle ventana |
| **Overlay** | Ventana flotante siempre visible durante grabación con timer MM:SS |
| **Auto-paste** | Transcripción se pega automáticamente en la ventana activa (Ctrl+V simulado) |
| **Crash recovery** | Sidecar se reinicia automáticamente con backoff exponencial (1s→32s) |
| **Health check** | Monitoreo cada 5 segundos, eventos emitidos al frontend |
| **Bundle size** | ~13 MB EXE vs ~45 MB Python bundle (CustomTkinter) |
| **Cold start** | <1s vs ~5s (Python import chain) |

## What's Removed

| Feature | Motivo |
|---------|--------|
| **Flet UI** | Reemplazada por Tauri v2 + Svelte 5 (más estable, mejor rendimiento) |
| **ui_flet/ directory** | Eliminado del proyecto |
| **Flet dependencies** | flet, flet-desk removidos de requirements.txt |

---

## Tech Stack Comparison

| Layer | Legacy (v0.15.0) | Tauri (v2.0.0) |
|-------|-------------------|-----------------|
| UI Framework | CustomTkinter / Flet | Tauri v2 + Svelte 5 |
| Backend | Python (all-in-one) | Rust (UI) + Python (sidecar) |
| Hotkeys | Python `keyboard` lib | Rust `tauri-plugin-global-shortcut` |
| System tray | CustomTkinter | Tauri native |
| Clipboard | pyperclip | arboard (Rust) |
| Key simulation | pyautogui | enigo (Rust) |
| Bundle | Python + PyInstaller | Native EXE + MSI |
| Size | ~45 MB | ~13 MB EXE / ~5 MB MSI |
| Cold start | ~5s | <1s |
