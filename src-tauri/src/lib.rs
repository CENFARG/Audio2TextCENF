use std::sync::Mutex;
use std::process::{Child, Command};
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
    r#"{"record":"Ctrl+Shift+R","cancel":"Escape"}"#.into()
}

#[tauri::command]
fn set_hotkey(name: String, binding: String) -> String {
    format!(r#"{{"{}":"{}"}}"#, name, binding)
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_global_shortcut::Builder::new().build())
        .setup(|app| {
            // Register default global shortcut: Ctrl+Shift+R for recording
            let handle = app.handle().clone();
            #[cfg(desktop)]
            {
                use tauri_plugin_global_shortcut::GlobalShortcutExt;
                if let Err(err) = app.global_shortcut().register("Ctrl+Shift+R") {
                    eprintln!("Failed to register global shortcut: {}", err);
                }
                let _ = handle;
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
