//! Audio2Text Tauri v2 shell — manages backend process, hotkeys, overlay, tray, and IPC.

pub mod clipboard;
pub mod hotkeys;
pub mod overlay;
pub mod tray;

use overlay::{create_overlay_window, hide_overlay, show_overlay, start_timer, OverlayState};
use std::sync::Arc;
use std::sync::Mutex;
use std::process::{Child, Command};
use tauri::Emitter;
use tauri::Listener;
use tauri::Manager;
use tauri_plugin_global_shortcut::GlobalShortcutExt;

static BACKEND: Mutex<Option<Child>> = Mutex::new(None);

/// Single Owner HotkeyState — single source of truth for global hotkey binding.
/// Managed via Tauri state, Mutex-protected, init from defaults.yaml or F9.
pub struct HotkeyState {
    pub current: Mutex<String>,
}

fn load_initial_hotkey() -> String {
    // Try multiple candidate paths for defaults.yaml
    let candidates = [
        "audio2text/config/defaults.yaml",
        "audio2text\\config\\defaults.yaml",
        "../audio2text/config/defaults.yaml",
        "config/defaults.yaml",
        "./audio2text/config/defaults.yaml",
    ];
    for path in candidates {
        if let Ok(content) = std::fs::read_to_string(path) {
            for line in content.lines() {
                let trimmed = line.trim();
                // look for record_toggle: value
                if trimmed.starts_with("record_toggle") {
                    if let Some(colon) = trimmed.find(':') {
                        let raw = trimmed[colon + 1..].trim().trim_matches('"').trim_matches('\'').trim();
                        if !raw.is_empty() {
                            // Normalize: parse to validate, if ok return canonical F9 if f9 else keep original
                            let candidate = raw.trim().to_string();
                            if hotkeys::parse_shortcut_string(&candidate).is_ok() {
                                // Canonicalize single F9 case to uppercase
                                if candidate.to_lowercase() == "f9" {
                                    return "F9".to_string();
                                }
                                // For other combos like Ctrl+Shift+R keep as-is but ensure parse works
                                return candidate;
                            }
                        }
                    }
                }
            }
        }
    }
    "F9".to_string()
}

// Single Owner State Machine — single sidecar: audio2text/main.py (FastAPI 8765).
// DEBT: raw Command spawn is kept for now. Ideal is tauri_plugin_shell::ShellExt::sidecar("audio2text")
// (requires compiled binary via externalBin/sidecar). When sidecar binary is ready,
// replace Command::new with app.shell().sidecar("audio2text").spawn().
// Invariant: never spawn backend/sidecar_entry.py — that path is dead code.

#[tauri::command]
fn toggle_recording(app: tauri::AppHandle, overlay: tauri::State<Arc<OverlayState>>) -> String {
    let op = uuid::Uuid::new_v4().to_string();
    if overlay.is_active() {
        // Stop: hide overlay + emit stopped; frontend calls POST /transcribe/stop for text
        overlay.stop();
        let _ = app.emit("recording:stopped", serde_json::json!({ "operation_id": op }));
        log::info!("toggle_recording -> stopped (op {})", op);
    } else {
        // Start: ensure backend is up (spawned at startup, idempotent), show overlay + emit started
        if !ensure_backend_running() {
            log::warn!("toggle_recording: backend not available, still showing overlay");
        }
        let _is_new = overlay.start();
        let _ = app.emit("recording:started", serde_json::json!({ "operation_id": op }));
        log::info!("toggle_recording -> started (op {})", op);
    }
    format!(r#"{{"status":"ok","operation_id":"{}"}}"#, op)
}

#[tauri::command]
fn start_backend(app: tauri::AppHandle, overlay: tauri::State<Arc<OverlayState>>) -> Result<String, String> {
    let mut guard = BACKEND.lock().map_err(|e| e.to_string())?;
    if guard.is_some() {
        // Already running — ensure overlay is active and emit
        let is_new = overlay.start();
        let _ = app.emit("recording:started", serde_json::json!({ "operation_id": uuid::Uuid::new_v4().to_string() }));
        if is_new {
            log::info!("start_backend: already running, emitted recording:started (is_new={})", is_new);
        }
        return Ok(r#"{"status":"already_running"}"#.into());
    }
    let operation_id = uuid::Uuid::new_v4().to_string();
    let child = spawn_backend()?;
    *guard = Some(child);
    drop(guard);
    let is_new = overlay.start();
    let _ = app.emit("recording:started", serde_json::json!({ "operation_id": operation_id }));
    if is_new {
        log::info!("start_backend: started backend + emitted recording:started (is_new true)");
    }
    Ok(format!(r#"{{"status":"started","operation_id":"{}"}}"#, operation_id))
}

/// Spawn the FastAPI sidecar (audio2text/main.py) with robust CWD resolution.
/// Never kill on stop — the backend is the session owner for settings + capture.
fn spawn_backend() -> Result<std::process::Child, String> {
    // Resolve repo root from CARGO_MANIFEST_DIR (src-tauri) => repo root = parent
    let manifest_dir = std::env::var("CARGO_MANIFEST_DIR").map(std::path::PathBuf::from);
    let repo_root: std::path::PathBuf = match manifest_dir {
        Ok(dir) => dir.parent().unwrap_or(&dir).to_path_buf(),
        Err(_) => std::env::current_dir().map_err(|e| e.to_string())?,
    };
    let python = repo_root.join(".venv").join("Scripts").join("python.exe");
    let main_py = repo_root.join("audio2text").join("main.py");
    if !python.exists() {
        return Err(format!("Python venv not found at {}", python.display()));
    }
    if !main_py.exists() {
        return Err(format!("backend entry not found at {}", main_py.display()));
    }
    log::info!("spawn_backend: python={} main={}", python.display(), main_py.display());
    Command::new(&python)
        .arg(&main_py)
        .current_dir(&repo_root)
        .stdout(std::process::Stdio::null())
        .stderr(std::process::Stdio::null())
        .spawn()
        .map_err(|e| format!("Failed to start backend: {}", e))
}

/// Spawn the backend once at app startup (Single Owner: session begins with backend up).
fn ensure_backend_running() -> bool {
    let should_spawn = BACKEND.lock().map(|g| g.is_none()).unwrap_or(true);
    if !should_spawn {
        return true;
    }
    match spawn_backend() {
        Ok(child) => {
            if let Ok(mut guard) = BACKEND.lock() {
                if guard.is_none() {
                    *guard = Some(child);
                    log::info!("ensure_backend_running: backend spawned at startup");
                    return true;
                }
            }
            false
        }
        Err(e) => {
            log::warn!("ensure_backend_running: spawn failed: {}", e);
            false
        }
    }
}

#[tauri::command]
fn stop_backend(app: tauri::AppHandle, overlay: tauri::State<Arc<OverlayState>>) -> Result<String, String> {
    // Single Owner: NEVER kill the backend process — it owns settings + capture session.
    // Stopping just hides overlay + emits recording:stopped. The frontend calls
    // POST /transcribe/stop to get the transcription text (via recording.svelte.ts).
    overlay.stop();
    let _ = app.emit("recording:stopped", serde_json::json!({ "operation_id": uuid::Uuid::new_v4().to_string() }));
    Ok(r#"{"status":"stopped"}"#.into())
}

#[tauri::command]
fn get_backend_status() -> String {
    let guard = BACKEND.lock().ok();
    let running = guard.as_ref().and_then(|g| g.as_ref()).is_some();
    format!(r#"{{"running":{},"pid":null}}"#, running)
}

#[tauri::command]
fn get_hotkeys(state: tauri::State<HotkeyState>) -> String {
    let current = state.current.lock().map(|g| g.clone()).unwrap_or_else(|_| "F9".to_string());
    format!(r#"{{"record":"{}","cancel":"Escape"}}"#, current)
}

#[tauri::command]
fn set_hotkey(app: tauri::AppHandle, state: tauri::State<HotkeyState>, name: String, binding: String) -> String {
    if name != "record" {
        // Only record is managed; return current for other names
        let cur = state.current.lock().map(|g| g.clone()).unwrap_or_else(|_| "F9".to_string());
        return format!(r#"{{"record":"{}","cancel":"Escape"}}"#, cur);
    }
    let old = state.current.lock().map(|g| g.clone()).unwrap_or_else(|_| "F9".to_string());
    // Validate binding
    if hotkeys::parse_shortcut_string(&binding).is_err() {
        log::warn!("set_hotkey: invalid binding '{}', fallback to F9", binding);
        if let Ok(mut guard) = state.current.lock() {
            *guard = "F9".to_string();
        }
        let _ = app.emit("hotkey:error", serde_json::json!({ "error": "Formato inválido, fallback F9", "binding": binding, "fallback": "F9" }));
        // Try to re-register F9 non-fatal
        let _ = hotkeys::register_global_hotkey(&app, "F9", move |a| {
            let _ = a.emit("hotkey:toggle_recording", ());
        });
        return r#"{"record":"F9","error":"invalid_format","fallback":"F9"}"#.into();
    }

    // Try to unregister old binding (ignore errors)
    if let Ok((mods, code)) = hotkeys::parse_shortcut_string(&old) {
        let shortcut = tauri_plugin_global_shortcut::Shortcut::new(Some(mods), code);
        let _ = app.global_shortcut().unregister(shortcut);
    }

    // Try to register new binding
    let binding_clone = binding.clone();
    let register_result = hotkeys::register_global_hotkey(&app, &binding, move |a| {
        let _ = a.emit("hotkey:toggle_recording", ());
    });

    match register_result {
        Ok(()) => {
            if let Ok(mut guard) = state.current.lock() {
                *guard = binding_clone.clone();
            }
            let _ = app.emit("hotkey:changed", serde_json::json!({ "record": binding_clone }));
            log::info!("set_hotkey: changed '{}' -> '{}'", old, binding_clone);
            format!(r#"{{"record":"{}"}}"#, binding_clone)
        }
        Err(e) => {
            let msg = e.to_string();
            // Non-fatal: keep old, emit error, return Ok payload with error
            log::warn!("set_hotkey: failed to register '{}' (keeping '{}'): {}", binding, old, msg);
            let _ = app.emit("hotkey:error", serde_json::json!({ "error": msg, "binding": binding, "current": old }));
            // Try to restore old registration
            let _ = hotkeys::register_global_hotkey(&app, &old, move |a| {
                let _ = a.emit("hotkey:toggle_recording", ());
            });
            format!(r#"{{"record":"{}","error":"{}"}}"#, old, msg)
        }
    }
}

#[tauri::command]
fn auto_paste(text: String) -> Result<String, String> {
    clipboard::auto_paste(&text)?;
    Ok(r#"{"status":"ok","pasted":true}"#.into())
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    env_logger::init();

    let overlay_state = Arc::new(OverlayState::new());
    let initial_hotkey = load_initial_hotkey();
    let hotkey_state = HotkeyState {
        current: Mutex::new(initial_hotkey.clone()),
    };

    tauri::Builder::default()
        // Single-instance guard: focus existing window if second instance launched
        .plugin(tauri_plugin_single_instance::init(|app, _args, _cwd| {
            if let Some(w) = app.get_webview_window("main") {
                let _ = w.show();
                let _ = w.set_focus();
            }
        }))
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_global_shortcut::Builder::new().build())
        .manage(overlay_state.clone())
        .manage(hotkey_state)
        .setup(move |app| {
            log::info!("Audio2Text Tauri v2 started");

            // Single Owner: spawn FastAPI backend FIRST so settings/capture are live from t=0.
            // Non-fatal: app still opens if python venv missing (UI shows errors).
            ensure_backend_running();

            // Create overlay window (hidden by default)
            if let Err(e) = create_overlay_window(app) {
                log::error!("Failed to create overlay: {}", e);
            }

            // Register default global hotkey from HotkeyState (single owner, not hardcode)
            let state_binding = app
                .state::<HotkeyState>()
                .current
                .lock()
                .map(|g| g.clone())
                .unwrap_or_else(|_| initial_hotkey.clone());
            if let Err(e) = hotkeys::register_global_hotkey(
                app.handle(),
                &state_binding,
                move |app| {
                    let _ = app.emit("hotkey:toggle_recording", ());
                },
            ) {
                log::error!("Failed to register hotkey '{}': {}", state_binding, e);
                let _ = app.emit("hotkey:error", serde_json::json!({ "error": e, "binding": state_binding }));
            } else {
                log::info!("Hotkey '{}' registered (single owner)", state_binding);
            }

            // Create system tray
            if let Err(e) = tray::create_system_tray(app) {
                log::error!("Failed to create tray: {}", e);
            }

            // Listen for recording events to control overlay — single-instance guard
            // `setup` runs once, so these listeners are registered exactly once.
            // `OverlayState::start()` is idempotent and `start_timer` has its own
            // single-instance guard, so duplicate `recording:started` never spawns a second tick task.
            let overlay_for_started = overlay_state.clone();
            let app_handle_started = app.handle().clone();
            app.listen("recording:started", move |_| {
                let is_new = overlay_for_started.start();
                let _ = show_overlay(&app_handle_started);
                if is_new {
                    start_timer(app_handle_started.clone(), overlay_for_started.clone());
                }
            });

            let overlay_for_stopped = overlay_state.clone();
            let app_handle_stopped = app.handle().clone();
            app.listen("recording:stopped", move |_| {
                overlay_for_stopped.stop();
                let _ = hide_overlay(&app_handle_stopped);
            });

            Ok(())
        })
        .invoke_handler(tauri::generate_handler![
            toggle_recording,
            start_backend,
            stop_backend,
            get_backend_status,
            get_hotkeys,
            set_hotkey,
            auto_paste,
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
