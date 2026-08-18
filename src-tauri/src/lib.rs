//! Audio2Text Tauri v2 shell — manages backend process, hotkeys, and IPC.

pub mod hotkeys;

use std::sync::Mutex;
use std::process::{Child, Command};
use tauri::Emitter;
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
    r#"{"record":"Ctrl+Alt+F10","cancel":"Escape"}"#.into()
}

#[tauri::command]
fn set_hotkey(name: String, binding: String) -> String {
    format!(r#"{{"{}":"{}"}}"#, name, binding)
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    env_logger::init();

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
        .setup(|app| {
            log::info!("Audio2Text Tauri v2 started");

            // Register default global hotkey: Ctrl+Alt+F10 for recording toggle
            let app_handle = app.handle().clone();
            if let Err(e) = hotkeys::register_global_hotkey(
                app.handle(),
                "Ctrl+Alt+F10",
                move |app| {
                    let _ = app.emit("hotkey:toggle_recording", ());
                },
            ) {
                log::error!("Failed to register hotkey: {}", e);
                let _ = app.emit("hotkey:error", serde_json::json!({ "error": e }));
            }

            Ok(())
        })
        .invoke_handler(tauri::generate_handler![
            toggle_recording,
            start_backend,
            stop_backend,
            get_backend_status,
            get_hotkeys,
            set_hotkey,
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
