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

static BACKEND: Mutex<Option<Child>> = Mutex::new(None);

#[tauri::command]
fn toggle_recording() -> String {
    r#"{"status":"ok"}"#.into()
}

#[tauri::command]
fn start_backend() -> Result<String, String> {
    let mut guard = BACKEND.lock().map_err(|e| e.to_string())?;
    if guard.is_some() {
        return Ok(r#"{"status":"already_running"}"#.into());
    }
    let child = Command::new(".venv/Scripts/python.exe")
        .arg("audio2text/main.py")
        .spawn()
        .map_err(|e| format!("Failed to start backend: {}", e))?;
    *guard = Some(child);
    Ok(r#"{"status":"started"}"#.into())
}

#[tauri::command]
fn stop_backend() -> Result<String, String> {
    let mut guard = BACKEND.lock().map_err(|e| e.to_string())?;
    if let Some(mut child) = guard.take() {
        child.kill().map_err(|e| format!("Failed to stop: {}", e))?;
        child.wait().ok();
        Ok(r#"{"status":"stopped"}"#.into())
    } else {
        Ok(r#"{"status":"not_running"}"#.into())
    }
}

#[tauri::command]
fn get_backend_status() -> String {
    let guard = BACKEND.lock().ok();
    let running = guard.as_ref().and_then(|g| g.as_ref()).is_some();
    format!(r#"{{"running":{},"pid":null}}"#, running)
}

#[tauri::command]
fn get_hotkeys() -> String {
    r#"{"record":"F9","cancel":"Escape"}"#.into()
}

#[tauri::command]
fn set_hotkey(name: String, binding: String) -> String {
    format!(r#"{{"{}":"{}"}}"#, name, binding)
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
        .setup(move |app| {
            log::info!("Audio2Text Tauri v2 started");

            // Create overlay window (hidden by default)
            if let Err(e) = create_overlay_window(app) {
                log::error!("Failed to create overlay: {}", e);
            }

            // Register default global hotkey: F9 for recording toggle
            if let Err(e) = hotkeys::register_global_hotkey(
                app.handle(),
                "F9",
                move |app| {
                    let _ = app.emit("hotkey:toggle_recording", ());
                },
            ) {
                log::error!("Failed to register hotkey: {}", e);
                let _ = app.emit("hotkey:error", serde_json::json!({ "error": e }));
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
