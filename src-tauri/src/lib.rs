#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    env_logger::init();

    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_global_shortcut::Builder::new().build())
        .plugin(tauri_plugin_clipboard_manager::init())
        .setup(|_app| {
            log::info!("Audio2Text Tauri v2 started");
            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
