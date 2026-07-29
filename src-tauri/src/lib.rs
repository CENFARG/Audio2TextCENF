use tauri::Manager;

#[tauri::command]
fn toggle_recording() -> String {
    r#"{"status":"ok"}"#.into()
}

#[tauri::command]
fn start_backend(app: tauri::AppHandle) -> Result<String, String> {
    use tauri_plugin_shell::ShellExt;
    let _ = app;
    Ok(r#"{"status":"started"}"#.into())
}

#[tauri::command]
fn stop_backend() -> Result<String, String> {
    Ok(r#"{"status":"stopped"}"#.into())
}

#[tauri::command]
fn get_backend_status() -> String {
    r#"{"running":false,"pid":null}"#.into()
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