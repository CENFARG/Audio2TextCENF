pub mod commands;
pub mod sidecar;

use sidecar::{SidecarState, start_health_check};
use std::sync::Arc;
use std::time::Duration;

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    env_logger::init();

    let sidecar_state = Arc::new(SidecarState::new());
    let sidecar_for_setup = Arc::clone(&sidecar_state);

    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_global_shortcut::Builder::new().build())
        .plugin(tauri_plugin_clipboard_manager::init())
        .manage(sidecar_state)
        .invoke_handler(tauri::generate_handler![
            commands::start_recording,
            commands::stop_recording,
            commands::get_config,
            commands::save_config,
            commands::get_history,
        ])
        .setup(move |app| {
            log::info!("Audio2Text Tauri v2 started");

            // Spawn the Python sidecar process
            let python = if cfg!(target_os = "windows") {
                "python"
            } else {
                "python3"
            };
            match sidecar_for_setup.spawn(python, "backend.sidecar_entry") {
                Ok(()) => {
                    log::info!("Sidecar spawned successfully");
                    start_health_check(
                        sidecar_for_setup,
                        app.handle().clone(),
                        Duration::from_secs(5),
                    );
                }
                Err(e) => {
                    log::error!("Failed to spawn sidecar: {}", e);
                }
            }

            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
