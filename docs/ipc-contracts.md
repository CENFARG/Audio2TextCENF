# IPC Contracts — Audio2Text Tauri v2

This document defines the IPC (Inter-Process Communication) contracts between the Tauri frontend (Svelte 5) and the Python sidecar process. All communication uses newline-delimited JSON over stdin/stdout.

## Overview

```
┌──────────────────┐     stdin (JSON)      ┌─────────────────────┐
│  Tauri Frontend   │ ───────────────────►  │  Python Sidecar     │
│  (Svelte 5)       │ ◄───────────────────  │  (sidecar_entry.py) │
└──────────────────┘     stdout (JSON)      └─────────────────────┘
```

- **Direction**: Frontend → Sidecar for commands; Sidecar → Frontend for events (via Tauri emit).
- **Format**: One JSON object per line, no streaming, no binary.
- **Encoding**: UTF-8.

---

## TypeScript Type Definitions

Source: `src/lib/types.ts`

```ts
/** IPC command types — sent from Tauri frontend to sidecar. */

export interface StartRecordingCmd {
  command: "start_recording";
}

export interface StopRecordingCmd {
  command: "stop_recording";
}

export interface GetConfigCmd {
  command: "get_config";
}

export interface SaveConfigCmd {
  command: "save_config";
  data: Record<string, unknown>;
}

export interface GetHistoryCmd {
  command: "get_history";
}

export type IpcCommand =
  | StartRecordingCmd
  | StopRecordingCmd
  | GetConfigCmd
  | SaveConfigCmd
  | GetHistoryCmd;

/** IPC event types — emitted from sidecar to Tauri frontend. */

export interface TranscriptionReadyEvent {
  event: "transcription_ready";
  data: {
    operation_id: string;
    text: string;
    duration: number;
    language: string;
  };
}

export interface RecordingStartedEvent {
  event: "recording_started";
  data: {
    timestamp: number;
  };
}

export interface RecordingStoppedEvent {
  event: "recording_stopped";
  data: {
    timestamp: number;
    duration: number;
  };
}

export interface StatusUpdateEvent {
  event: "status_update";
  data: {
    message: string;
    color: string;
  };
}

export interface HealthCheckEvent {
  event: "health_check";
  data: {
    alive: boolean;
    uptime: number;
  };
}

export type IpcEvent =
  | TranscriptionReadyEvent
  | RecordingStartedEvent
  | RecordingStoppedEvent
  | StatusUpdateEvent
  | HealthCheckEvent;

/** Command response envelope. */

export interface CommandResponse<T = unknown> {
  status: "ok" | "error";
  data?: T;
  error?: string;
}
```

---

## Rust Command Enum

Source: `src-tauri/src/sidecar.rs`

```rust
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(tag = "command")]
pub enum SidecarCommand {
    #[serde(rename = "start_recording")]
    StartRecording,
    #[serde(rename = "stop_recording")]
    StopRecording,
    #[serde(rename = "get_config")]
    GetConfig,
    #[serde(rename = "save_config")]
    SaveConfig { data: serde_json::Value },
    #[serde(rename = "get_history")]
    GetHistory,
    #[serde(rename = "register_hotkey")]
    RegisterHotkey { hotkey: String },
}
```

---

## Commands

### `start_recording`

Starts audio recording via the sidecar.

**Request:**
```json
{"command": "start_recording"}
```

**Response (success):**
```json
{
  "status": "ok",
  "data": {
    "recording": true
  }
}
```

**Response (error):**
```json
{
  "status": "error",
  "error": "Sidecar not running"
}
```

**Side effect:** Tauri emits `recording:started` event to all listeners.

**Frontend call:**
```ts
import { invoke } from "@tauri-apps/api/core";
const result = await invoke("start_recording");
```

---

### `stop_recording`

Stops audio recording via the sidecar.

**Request:**
```json
{"command": "stop_recording"}
```

**Response (success):**
```json
{
  "status": "ok",
  "data": {
    "recording": false
  }
}
```

**Side effect:** Tauri emits `recording:stopped` event to all listeners.

**Frontend call:**
```ts
const result = await invoke("stop_recording");
```

---

### `get_config`

Returns the current configuration from `config.json`.

**Request:**
```json
{"command": "get_config"}
```

**Response (success):**
```json
{
  "status": "ok",
  "data": {
    "app_version": "0.15.0",
    "audio_path": "./audio",
    "hotkey": "f9",
    "record_mode": "toggle",
    "default_language": "es",
    "auto_paste_text": true,
    "asr_provider": "groq",
    "nvidia_enabled": false,
    "faster_whisper_enabled": false
  }
}
```

**Response (file missing):**
```json
{
  "status": "ok",
  "data": {}
}
```

**Frontend call:**
```ts
const result = await invoke("get_config");
const config = result.data;
```

---

### `save_config`

Merges provided data into the existing `config.json` and saves it.

**Request:**
```json
{
  "command": "save_config",
  "data": {
    "hotkey": "f10",
    "default_language": "en"
  }
}
```

**Response (success):**
```json
{
  "status": "ok",
  "data": {
    "app_version": "0.15.0",
    "hotkey": "f10",
    "default_language": "en",
    "auto_paste_text": true
  }
}
```

The response `data` contains the **full merged config** after save.

**Frontend call:**
```ts
const result = await invoke("save_config", {
  config: { hotkey: "f10" }
});
```

---

### `get_history`

Returns transcription history.

**Request:**
```json
{"command": "get_history"}
```

**Response (success):**
```json
{
  "status": "ok",
  "data": []
}
```

> Note: The current sidecar implementation returns an empty array. Full history support is pending backend integration.

**Frontend call:**
```ts
const result = await invoke("get_history");
const entries = result.data;
```

---

### `auto_paste`

Copies text to the system clipboard and simulates Ctrl+V paste into the active window. This command is handled directly by the Rust side (not forwarded to the sidecar).

**Request (via Tauri invoke):**
```ts
await invoke("auto_paste", { text: "Hello, World!" });
```

**Response:**
```json
{
  "status": "ok",
  "data": {
    "pasted": true
  }
}
```

**Implementation:** Uses `arboard` for clipboard write and `enigo` for Ctrl+V simulation.

---

### `register_hotkey`

Registers a global hotkey through the Python sidecar (fallback mechanism). Primary hotkey registration is handled natively by Rust via `tauri-plugin-global-shortcut`.

**Request:**
```json
{
  "command": "register_hotkey",
  "hotkey": "Ctrl+Alt+F9"
}
```

**Response (success):**
```json
{
  "status": "ok",
  "data": {
    "registered": true
  }
}
```

**Response (error):**
```json
{
  "status": "error",
  "error": "Missing 'hotkey' field"
}
```

---

## Events

Events are emitted by the Tauri backend and received by the frontend via `@tauri-apps/api/event`.

### `recording:started`

Emitted when recording starts successfully.

```ts
import { listen } from "@tauri-apps/api/event";

const unlisten = await listen("recording:started", () => {
  console.log("Recording started");
});
```

**Payload:** `()` (empty — event presence is the signal)

---

### `recording:stopped`

Emitted when recording stops successfully.

```ts
const unlisten = await listen("recording:stopped", () => {
  console.log("Recording stopped");
});
```

**Payload:** `()` (empty)

---

### `health_check`

Emitted every 5 seconds by the health check loop. Reports sidecar liveness and uptime.

```ts
const unlisten = await listen("health_check", (event) => {
  const { alive, uptime } = event.payload;
  if (!alive) {
    console.warn(`Sidecar dead. Uptime was ${uptime}s`);
  }
});
```

**Payload:**
```json
{
  "event": "health_check",
  "data": {
    "alive": true,
    "uptime": 120
  }
}
```

| Field   | Type    | Description                            |
|---------|---------|----------------------------------------|
| `alive` | boolean | Whether the sidecar process is alive   |
| `uptime`| number  | Seconds since the sidecar was spawned  |

---

### `transcription-ready`

Emitted when a transcription result is available (future — requires backend integration).

```ts
const unlisten = await listen("transcription-ready", (event) => {
  const { operation_id, text, duration, language } = event.payload;
  console.log(`Transcription (${language}, ${duration}s): ${text}`);
});
```

**Payload:**
```json
{
  "event": "transcription_ready",
  "data": {
    "operation_id": "abc-123",
    "text": "Hola, esto es una transcripción de prueba.",
    "duration": 12.5,
    "language": "es"
  }
}
```

| Field          | Type   | Description                            |
|----------------|--------|----------------------------------------|
| `operation_id` | string | Unique identifier for the operation    |
| `text`         | string | Transcribed text                       |
| `duration`     | number | Recording duration in seconds          |
| `language`     | string | Detected language code (e.g. "es")     |

---

### `recording-started`

Alternative event name emitted by the sidecar directly (for sidecar-to-frontend direct events).

```json
{
  "event": "recording_started",
  "data": {
    "timestamp": 1699900000000
  }
}
```

---

### `recording-stopped`

Alternative event name emitted by the sidecar directly.

```json
{
  "event": "recording_stopped",
  "data": {
    "timestamp": 1699900012500,
    "duration": 12.5
  }
}
```

---

### `status-update`

Emitted by the sidecar to update the UI status bar.

```json
{
  "event": "status_update",
  "data": {
    "message": "Transcription complete",
    "color": "#4CAF50"
  }
}
```

| Field     | Type   | Description                             |
|-----------|--------|-----------------------------------------|
| `message` | string | Human-readable status message           |
| `color`   | string | CSS color for the status indicator      |

---

## Response Envelope

All commands return the same envelope structure:

```ts
interface CommandResponse<T = unknown> {
  status: "ok" | "error";
  data?: T;
  error?: string;
}
```

| Field   | Type     | Condition                  |
|---------|----------|----------------------------|
| `status`| string   | Always present             |
| `data`  | any      | Present on `ok` responses  |
| `error` | string   | Present on `error` responses |

---

## Global Hotkeys (Rust-native)

Hotkeys are registered directly in Rust, not via the sidecar. The default hotkey is **Ctrl+Alt+F9** (toggle recording).

### Supported Modifiers
`Ctrl` / `Control`, `Alt`, `Shift`, `Super` / `Meta` / `Win` / `Cmd`

### Supported Keys
F1–F24, a–z, 0–9, Space, Enter, Tab, Escape, Backspace, Delete, Home, End, PageUp, PageDown, arrow keys

### Example
```
Ctrl+Alt+F9  → Toggle recording
Ctrl+Shift+S → Custom action
F12          → Single key (no modifier)
```

Registration is done at app startup in `hotkeys.rs`:
```rust
let shortcut = Shortcut::new(Some(Modifiers::CONTROL | Modifiers::ALT), Code::F9);
app.global_shortcut().on_shortcut(shortcut, ...)?;
```

---

## Capability Permissions

Source: `src-tauri/capabilities/default.json`

```json
{
  "identifier": "default",
  "windows": ["main", "overlay"],
  "permissions": [
    "core:default",
    "shell:default",
    "shell:allow-execute",
    "shell:allow-spawn",
    "shell:allow-stdin-write",
    "global-shortcut:allow-register",
    "global-shortcut:allow-unregister",
    "global-shortcut:allow-is-registered",
    "clipboard-manager:allow-write-text",
    "clipboard-manager:allow-read-text"
  ]
}
```

---

## Error Handling

All errors follow the same pattern:

1. **Sidecar not running**: `"Sidecar not running"` — the process has crashed or hasn't started yet.
2. **No stdin/stdout handle**: `"No stdin handle"` / `"No stdout handle"` — process handles were taken.
3. **Write failure**: `"Write failed: ..."` — stdin pipe broken.
4. **Read failure**: `"Read failed: ..."` / `"Sidecar closed stdout"` — sidecar exited.
5. **Invalid JSON**: `"Invalid JSON from sidecar: ..."` — sidecar output is malformed.
6. **Unknown command**: `"Unknown command: ..."` — command string not recognized by the sidecar.
