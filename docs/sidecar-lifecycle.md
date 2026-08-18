# Sidecar Lifecycle — Audio2Text Tauri v2

The Python sidecar is a child process managed by the Tauri Rust backend. It handles audio processing, transcription, and configuration while the Rust layer manages the UI, system tray, hotkeys, and clipboard.

## Architecture

```
┌──────────────────────────────────────────────────┐
│  Tauri (Rust)                                     │
│  ┌─────────┐ ┌──────┐ ┌───────┐ ┌────────────┐  │
│  │ Commands │ │ Tray │ │Hotkeys│ │  Overlay   │  │
│  └────┬─────┘ └──┬───┘ └───┬───┘ └─────┬──────┘  │
│       │          │         │            │          │
│       └──────────┴─────────┴────────────┘          │
│                      │                             │
│              SidecarState (Arc<Mutex>)              │
│                      │                             │
│              stdin/stdout pipes                    │
└──────────────────────┼────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────┐
│  Python Sidecar (backend/sidecar_entry.py)        │
│  ┌──────────────────┐  ┌───────────────────────┐  │
│  │ JSON-line server │  │ Command handlers      │  │
│  │ stdin → stdout   │  │ start/stop/config/... │  │
│  └──────────────────┘  └───────────────────────┘  │
└──────────────────────────────────────────────────┘
```

## State Diagram

```
                    ┌─────────────┐
                    │   CREATED   │
                    │ SidecarState│
                    │    ::new()  │
                    └──────┬──────┘
                           │ spawn()
                           ▼
                    ┌─────────────┐
              ┌────►│   RUNNING   │◄────────────┐
              │     │  (alive)    │             │
              │     └──────┬──────┘             │
              │            │                    │
              │       is_alive()==false         │
              │            │                    │
              │            ▼                    │
              │     ┌─────────────┐             │
              │     │  CRASHED    │             │
              │     │  (dead)     │             │
              │     └──────┬──────┘             │
              │            │                    │
              │     exponential backoff         │
              │     (1s, 2s, 4s...)             │
              │            │                    │
              │        spawn()                  │
              │            │                    │
              │            └────────────────────┘
              │
              │ kill() / app.exit()
              ▼
        ┌─────────────┐
        │   STOPPED   │
        │  (killed)   │
        └─────────────┘
```

## Start — How the Sidecar is Spawned

### Location

`src-tauri/src/lib.rs:73-92`

### Spawn Sequence

1. **App setup** runs in `tauri::Builder::default().setup()`.
2. The Python executable is determined:
   - Windows: `"python"`
   - Other: `"python3"`
3. `SidecarState::spawn(python, "backend.sidecar_entry")` is called.
4. The sidecar process is spawned via `std::process::Command`:
   ```rust
   Command::new(python_path)
       .args(["-m", entry_module])  // runs: python -m backend.sidecar_entry
       .stdin(Stdio::piped())
       .stdout(Stdio::piped())
       .stderr(Stdio::null())       // stderr discarded
       .spawn()
   ```
5. On success, `start_health_check()` is launched with a 5-second interval.
6. On failure, the error is logged and the app continues without a sidecar.

### Spawn Details

| Parameter        | Value                    | Description                      |
|------------------|--------------------------|----------------------------------|
| `python_path`    | `"python"` (Windows)     | Python executable                |
| `entry_module`   | `"backend.sidecar_entry"`| Module to run (`python -m ...`)  |
| `stdin`          | `Stdio::piped()`         | For sending commands             |
| `stdout`         | `Stdio::piped()`         | For reading responses            |
| `stderr`         | `Stdio::null()`          | Discarded (no capture)           |

### What the Sidecar Does on Start

When `backend/sidecar_entry.py` starts:
1. Configures logging to stderr (which is discarded by the Rust side).
2. Enters a loop reading JSON lines from stdin.
3. For each valid JSON command, dispatches to the appropriate handler and writes a JSON response to stdout.

---

## Health Check — 5-Second Interval

### Location

`src-tauri/src/sidecar.rs:174-225`

### Health Check Loop

```rust
pub fn start_health_check(
    state: Arc<SidecarState>,
    app_handle: tauri::AppHandle,
    interval: Duration,  // 5 seconds
)
```

The health check runs on Tauri's async runtime (`tauri::async_runtime::spawn`):

1. **Sleep** for the configured interval (5 seconds).
2. **Check liveness**: `state.is_alive()` — checks if the `Child` handle exists.
3. **Get uptime**: `state.uptime_secs()` — seconds since last spawn.
4. **Emit event**: `health_check` with `{ alive, uptime }` payload.
5. **If dead**: Attempt restart with exponential backoff.

### What's Checked

| Check           | Method                        | Condition                      |
|-----------------|-------------------------------|--------------------------------|
| Process alive   | `inner.child.is_some()`       | `Child` handle exists          |
| Uptime          | `started_at.elapsed().as_secs`| Time since last spawn          |
| Recording state | `inner.is_recording`          | Whether recording is active    |

### Health Check Event

```json
{
  "event": "health_check",
  "data": {
    "alive": true,
    "uptime": 120
  }
}
```

---

## Crash Recovery — Exponential Backoff

### Location

`src-tauri/src/sidecar.rs:196-222`

### Backoff Formula

```rust
let backoff_ms = 1000 * 2u64.pow(restart_count.min(5));
```

### Backoff Table

| Attempt | `restart_count` | Delay (ms) | Delay (s) |
|---------|-----------------|------------|-----------|
| 1       | 0               | 1,000      | 1         |
| 2       | 1               | 2,000      | 2         |
| 3       | 2               | 4,000      | 4         |
| 4       | 3               | 8,000      | 8         |
| 5       | 4               | 16,000     | 16        |
| 6+      | 5 (capped)      | 32,000     | 32        |

The maximum backoff is capped at `2^5 = 32` seconds (the `.min(5)` clamp).

### Recovery Flow

```
Sidecar dies (is_alive() == false)
    │
    ├──► Log warning: "Sidecar dead, restarting in {backoff}ms (attempt {n})"
    │
    ├──► Sleep for backoff_ms
    │
    ├──► Call state.spawn(python, "backend.sidecar_entry")
    │       │
    │       ├──► Success: Sidecar running again, restart_count incremented
    │       │
    │       └──► Failure: Log error, wait for next health check cycle
    │
    └──► Next health check in 5s will detect and retry again if needed
```

### Key Behaviors

- **Backoff resets on successful spawn**: The `restart_count` increments each time, so backoff grows until the sidecar stays alive.
- **No max retry limit**: The loop runs indefinitely. A crashed sidecar will keep trying to restart.
- **Concurrent safety**: The `Mutex<SidecarInner>` prevents race conditions between health check and command sending.
- **Recording state preserved**: If recording was active when the sidecar crashed, the `is_recording` flag remains true. The next health check cycle will attempt to restart, but the UI should handle the interruption.

---

## Graceful Shutdown — SIGTERM → Cleanup → Exit

### Location

`src-tauri/src/sidecar.rs:147-155` and `src-tauri/src/tray.rs:69-71`

### Shutdown Sequence

When the user clicks "Quit" in the system tray or closes the window:

1. **Tray "Quit" handler** calls `app.exit(0)`.
2. Tauri's shutdown process begins.
3. **SidecarState::kill()** is called (if explicit cleanup is needed):
   ```rust
   pub fn kill(&self) -> Result<(), String> {
       let mut inner = self.inner.lock()?;
       if let Some(ref mut child) = inner.child {
           let _ = child.kill();   // TerminateProcess on Windows
           let _ = child.wait();   // Wait for process to exit
       }
       inner.child = None;
       Ok(())
   }
   ```
4. On Windows, `child.kill()` calls `TerminateProcess` (force kill).
5. `child.wait()` reaps the zombie process.
6. The `Child` handle is set to `None`.

### What Happens to the Sidecar

- **No SIGTERM on Windows**: Windows doesn't have SIGTERM. `child.kill()` calls `TerminateProcess` which is immediate and non-graceful.
- **The Python sidecar has no cleanup handler**: Since `stderr` is discarded and the process is killed via `TerminateProcess`, the sidecar has no opportunity to run `atexit` handlers or flush buffers.
- **Stdin pipe close**: When the Rust side drops the stdin handle, the Python sidecar's `for line in sys.stdin` loop will eventually exit (EOF), but this is only relevant if the process is not killed first.

### Potential Issue

If the sidecar is mid-transcription when killed, the transcription result may be lost. The sidecar does not persist partial results. This is an acceptable trade-off for the current implementation.

---

## Command Flow

### Sending a Command

```
Frontend (Svelte)
    │
    ▼ invoke("start_recording")
Tauri Command Handler (commands.rs)
    │
    ▼ state.send_command(&SidecarCommand::StartRecording)
SidecarState::send_command() (sidecar.rs)
    │
    ├── Lock Mutex<SidecarInner>
    ├── Take stdin handle from Child
    ├── Write JSON command + newline to stdin
    ├── Take stdout handle from Child
    ├── Read one line from stdout
    ├── Parse JSON response
    ├── Return stdin/stdout handles to Child
    └── Unlock Mutex
    │
    ▼
CommandResult (commands.rs)
    │
    ▼
Frontend receives CommandResponse
```

### Important: Handle Ownership

The `send_command` method **takes ownership** of stdin and stdout handles temporarily:

```rust
let mut stdin = child.stdin.take().ok_or("No stdin handle")?;
let stdout = child.stdout.take().ok_or("No stdout handle")?;
// ... do I/O ...
child.stdin = Some(stdin);
child.stdout = Some(reader.into_inner());
```

This means **only one command can be in flight at a time**. Concurrent commands will fail with "No stdin handle" or "No stdout handle".

---

## Restart Count

The `restart_count` field in `SidecarInner` tracks how many times the sidecar has been spawned:

```rust
struct SidecarInner {
    child: Option<Child>,
    started_at: Instant,
    restart_count: u32,    // Increments on each spawn()
    is_recording: bool,
}
```

- Increments by 1 each time `spawn()` is called (including the initial spawn).
- Used to calculate exponential backoff delay.
- Not reset on successful spawn — it monotonically increases for the lifetime of the app.

---

## Thread Safety

| Resource               | Synchronization            | Location                    |
|------------------------|----------------------------|-----------------------------|
| `SidecarInner`         | `Mutex<SidecarInner>`      | `sidecar.rs:37-38`          |
| `is_recording` (hotkey)| `AtomicBool`               | `hotkeys.rs:7`              |
| `OverlayState`         | `AtomicBool` + `Mutex<Option<Instant>>` | `overlay.rs:9-10` |
| `AppState` (Tauri)     | `Arc<SidecarState>`        | `lib.rs:18`                 |

The `SidecarState` is wrapped in `Arc` and shared across:
- The Tauri command handlers (via `State<'_, Arc<SidecarState>>`)
- The health check loop (via `Arc::clone`)
- The hotkey handler (via `Arc::clone`)
- The tray menu handler (via `Arc::clone`)
