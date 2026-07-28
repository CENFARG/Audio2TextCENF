# CES UI Components Specification

## Purpose

Svelte 5 frontend hosted inside the Tauri webview — five views (Transcribe, History, Settings, Info, Update) with shadcn-svelte components, WebSocket streaming, and rune-based state management. Replaces the Flet UI with identical functionality.

## Requirements

### Requirement: Navigation Shell

The app SHALL render a sidebar navigation with 5 tabs: Transcribe (mic icon), History (clock icon), Settings (gear icon), Info (info icon), Update (download icon). The active tab SHALL be highlighted with the accent color (`#DAA520`).

- Tab selection SHALL use Svelte 5 `$state` rune.
- View switching SHALL NOT cause full-page re-renders — only the content area updates.

#### Scenario: Navigate between views

- GIVEN the user is on the Transcribe view
- WHEN they click the Settings tab in the sidebar
- THEN the `$state` rune for `currentView` SHALL be `"settings"`
- AND the SettingsView component SHALL render in the content area
- AND the TranscribeView SHALL be unmounted or hidden

### Requirement: TranscribeView — Recording + Streaming

The TranscribeView SHALL contain: an AudioCapture record button, a TranscriptionPanel for live text, a RecordingOverlay with LED indicator and elapsed timer, a StatusBar, and a ContextBlocksSelector.

- Clicking the record button SHALL trigger `POST /api/v1/transcribe/start`.
- The WebSocket stream SHALL connect to `ws://127.0.0.1:8765/api/v1/transcribe/stream` directly from TypeScript.
- Partial frames SHALL append text to `$state` rune `transcriptionText`.
- A final frame SHALL stop the recording and persist the transcript.
- One automatic reconnect SHALL be attempted on WebSocket disconnection.
- The RecordingOverlay SHALL show a red/gray LED and MM:SS timer.

#### Scenario: Successful transcription stream

- GIVEN the user is on the TranscribeView and the backend is healthy
- WHEN the user clicks the record button
- THEN `POST /api/v1/transcribe/start` SHALL return `{ session_id }`
- AND the WS stream SHALL open
- AND partial text frames SHALL appear live in the TranscriptionPanel
- AND the RecordingOverlay SHALL show a red LED and running timer

#### Scenario: WebSocket reconnect on drop

- GIVEN an active WebSocket connection
- WHEN the connection drops unexpectedly
- THEN the client SHALL attempt one automatic reconnect
- AND IF the reconnect succeeds SHALL resume streaming
- AND IF the reconnect fails SHALL display an error snackbar

### Requirement: SettingsView — 8 Configuration Panels

The SettingsView SHALL render as a scrollable form with sections: Provider, Audio, Recording, UI, Post-processing, Blocks, Hotkey, Vocabulary.

- Provider section: Groq/NVIDIA API keys (password fields), ASR provider dropdown, faster-whisper model/device.
- Audio section: Path fields with browse button, max files, auto-cleanup toggle, save-audio toggle.
- Recording section: Record mode radio (toggle/hold), max time dropdown.
- UI section: Auto-paste, show-panel, start-with-Windows toggles.
- Post-processing: Enable toggle, model dropdown (groq/openai).
- Blocks: Task extractor, Summary, Keyword extractor toggles.
- Each field change SHALL trigger PUT `/api/v1/settings` with 400ms debounce.

#### Scenario: Auto-save on toggle change

- GIVEN the user is on the SettingsView
- WHEN the user toggles "Auto-paste" on
- THEN after 400ms the frontend SHALL call `PUT /api/v1/settings`
- AND the payload SHALL include `{ "auto_paste": true }`
- AND no other settings fields SHALL be affected

### Requirement: HistoryView — Search + Emoji

The HistoryView SHALL show a split layout: history list (left, expand=2) and detail panel + emoji picker (right, expand=1).

- A search input SHALL filter the list client-side by title/text.
- Selecting an item SHALL show full details: emoji, title, text, provider, created_at.
- The emoji picker SHALL allow assigning an emoji to the selected item via `PUT /api/v1/metadata/{id}`.
- Each item SHALL have a delete button calling `DELETE /api/v1/transcriptions/{id}`.

#### Scenario: Assign emoji to transcription

- GIVEN a transcription item is selected in the history list
- WHEN the user picks the "🎯" emoji from the picker
- THEN `PUT /api/v1/metadata/{id}` SHALL be called with `{ "emoji": "🎯" }`
- AND the detail panel SHALL show "🎯" prepended to the title

### Requirement: InfoView + UpdateView

- InfoView SHALL display: app version, credits, license (Apache 2.0), Python version, OS platform.
- UpdateView SHALL display: current version text, "Check for updates" button, status text, progress bar, loading spinner.
- The check button SHALL call `GET /api/v1/update/check` and display `has_update` status.

#### Scenario: Check for updates

- GIVEN the user is on the UpdateView
- WHEN the user clicks "Check for updates"
- THEN the loading spinner SHALL appear
- AND the button SHALL be disabled
- AND `GET /api/v1/update/check` SHALL be called
- AND IF `has_update` is true SHALL show the latest version as available
- AND the button SHALL be re-enabled

### Requirement: API Client — Typed HTTP + WebSocket

A TypeScript `APIClient` class SHALL provide typed methods for all 16 REST endpoints and WebSocket streaming.

- Endpoints: health, settings (GET/PUT), context-blocks, transcriptions (list, delete, metadata), transcribe (start/stop, WS stream), enhance, update-check.
- The client SHALL use the native `fetch` API for HTTP and the `WebSocket` browser API for streaming.
- Every endpoint SHALL return properly typed interfaces defined with Zod schemas.

#### Scenario: Typed settings response

- GIVEN the APIClient is initialized with `baseUrl: "http://127.0.0.1:8765"`
- WHEN `client.getSettings()` is called
- THEN a `GET /api/v1/settings` SHALL be issued
- AND the response SHALL be validated against a Zod schema
- AND the returned type SHALL be `SettingsConfig` with all expected fields

### Requirement: Global Hotkey Listener

A Svelte store SHALL subscribe to Tauri global-shortcut events. The store SHALL expose a `$state` rune for the current hotkey combination and provide a `register(key: string)` function.

#### Scenario: Hotkey triggers recording via Tauri IPC

- GIVEN a hotkey combination is registered via `tauri-plugin-global-shortcut`
- WHEN the user presses the registered shortcut
- THEN the Tauri event SHALL be received in the frontend
- AND the recording state rune SHALL toggle
- AND the UI SHALL reflect the new state without user interaction
