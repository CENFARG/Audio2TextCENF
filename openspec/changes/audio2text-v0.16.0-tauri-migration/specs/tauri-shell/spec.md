# Tauri Shell Specification

## Purpose

Container layer — Tauri v2 desktop shell that launches the Python backend as a sidecar process, exposes native OS features via Rust IPC commands, and hosts the Svelte 5 frontend.

## Requirements

### Requirement: Project Scaffold

The `src-tauri/` directory MUST be initialized via `create-tauri-app` with the Svelte template. The project SHALL use pnpm as package manager and Turborepo for monorepo orchestration.

- Cargo.toml SHALL declare tauri v2, serde, serde_json, and tauri-plugin-shell as dependencies.
- tauri.conf.json SHALL set window title `"Audio2Text"`, size `1100x760`, min size `800x600`, and `decorations: true`.
- The identifier SHALL be `com.cenf.audio2text`.

#### Scenario: Scaffold with correct metadata

- GIVEN a fresh project directory
- WHEN `create-tauri-app` runs with the SvelteKit template
- THEN `src-tauri/Cargo.toml` MUST contain `tauri = "2"` as a dependency
- AND `src-tauri/tauri.conf.json` MUST have `"identifier": "com.cenf.audio2text"`
- AND the window section MUST specify `"width": 1100`, `"height": 760`, `"minWidth": 800`, `"minHeight": 600`

### Requirement: Rust Sidecar — Python Backend Lifecycle

The Rust binary MUST launch the Python FastAPI backend as a Tauri sidecar process on application startup and terminate it on exit.

- `src-tauri/capabilities/default.json` SHALL grant `shell:allow-execute` for the sidecar.
- tauri.conf.json SHALL declare a `"sidecar"` entry pointing to the Python process.
- A Rust command `start_backend` SHALL spawn the sidecar and return `{ status: "started" | "already_running" }`.
- A Rust command `stop_backend` SHALL send SIGTERM to the child process and return `{ status: "stopped" }`.
- A Rust command `get_backend_status` SHALL return `{ running: bool, pid: number | null }`.
- Rust code MUST NOT exceed ~250 lines total.

#### Scenario: Sidecar start on app launch

- GIVEN the Tauri app starts
- WHEN the `setup` hook executes
- THEN the Python sidecar process MUST be spawned
- AND `get_backend_status` MUST return `{ running: true, pid: <non-null> }`

#### Scenario: Stop backend command

- GIVEN the backend is running
- WHEN `stop_backend` is invoked
- THEN the child process MUST be terminated
- AND `get_backend_status` MUST return `{ running: false, pid: null }`

### Requirement: Native OS Integration

The shell MUST provide Tauri plugins for window management, global hotkeys, and system tray.

- `tauri-plugin-global-shortcut` SHALL register `Ctrl+Shift+R` as the default toggle-recording hotkey.
- `tauri-plugin-shell` SHALL be used for sidecar execution.
- System tray SHALL show an icon with menu items: Show, Hide, Quit.
- Rust SHALL expose `toggle_recording`, `get_hotkeys`, `set_hotkey(key: string)`, and `show_tray` as IPC commands.

#### Scenario: Global shortcut triggers recording toggle

- GIVEN the app is running in the background
- WHEN the user presses `Ctrl+Shift+R`
- THEN the Rust IPC command `toggle_recording` MUST be invoked
- AND the frontend SHALL receive the event via Tauri event system
- AND the recording state SHALL toggle between idle and recording

#### Scenario: System tray quit

- GIVEN the app is running
- WHEN the user selects "Quit" from the system tray menu
- THEN the backend sidecar MUST be stopped first
- AND the Tauri window MUST be destroyed
- AND the app process MUST exit with code 0

### Requirement: Capabilities Security Model

The `capabilities/default.json` file SHALL define a minimal permission set.

- Permissions SHALL include: `core:default`, `shell:allow-execute`, `global-shortcut:allow-register`, `global-shortcut:allow-unregister`, `window:allow-close`, `window:allow-hide`, `window:allow-show`.

#### Scenario: Capability enforcement

- GIVEN the capabilities file is loaded
- WHEN a frontend API call attempts an unlisted permission
- THEN Tauri MUST reject the call with a permission denied error
- AND the app MUST NOT crash
