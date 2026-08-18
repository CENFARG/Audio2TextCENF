pub mod clipboard;
pub mod commands;
pub mod hotkeys;
pub mod overlay;
pub mod sidecar;
pub mod tray;

use overlay::{create_overlay_window, hide_overlay, show_overlay, start_timer, OverlayState};
use sidecar::{SidecarState, start_health_check};
use std::sync::Arc;
use std::time::Duration;
use tauri::Emitter;
use tauri::Listener;
use tauri::Manager;

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    env_logger::init();

    let sidecar_state = Arc::new(SidecarState::new());
    let sidecar_for_setup = Arc::clone(&sidecar_state);
    let sidecar_for_hotkey = Arc::clone(&sidecar_state);
    let sidecar_for_tray = Arc::clone(&sidecar_state);

    let overlay_state = Arc::new(OverlayState::new());

    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_global_shortcut::Builder::new().build())
        .plugin(tauri_plugin_clipboard_manager::init())
        .manage(sidecar_state)
        .manage(overlay_state.clone())
        .invoke_handler(tauri::generate_handler![
            commands::start_recording,
            commands::stop_recording,
            commands::get_config,
            commands::save_config,
            commands::get_history,
            commands::auto_paste,
            commands::clear_audio,
            commands::clear_transcriptions,
            commands::get_sidecar_status,
        ])
        .setup(move |app| {
            log::info!("Audio2Text Tauri v2 started");

            // Create overlay window (hidden by default)
            if let Err(e) = create_overlay_window(app) {
                log::error!("Failed to create overlay: {}", e);
            }

            // Register global hotkey (Ctrl+Alt+F9)
            if let Err(e) = hotkeys::register_default_hotkey(app.handle(), sidecar_for_hotkey) {
                log::error!("Failed to register hotkey: {}", e);
                let _ = app.emit("hotkey:error", serde_json::json!({ "error": e.to_string() }));
            }

            // Create system tray
            if let Err(e) = tray::create_system_tray(app, sidecar_for_tray) {
                log::error!("Failed to create tray: {}", e);
            }

            // Listen for recording events to control overlay
            let overlay_for_started = overlay_state.clone();
            let app_handle_started = app.handle().clone();
            app.listen("recording:started", move |_| {
                overlay_for_started.start();
                let _ = show_overlay(&app_handle_started);
                start_timer(app_handle_started.clone(), overlay_for_started.clone());
            });

            let overlay_for_stopped = overlay_state.clone();
            let app_handle_stopped = app.handle().clone();
            app.listen("recording:stopped", move |_| {
                overlay_for_stopped.stop();
                let _ = hide_overlay(&app_handle_stopped);
            });

            // Spawn the Python sidecar process — MUST use venv Python for dependencies
            // Resolve absolute path to venv Python so it works regardless of working dir
            let cwd = std::env::current_dir().unwrap_or_else(|_| std::path::PathBuf::from("."));
            let python = if cfg!(target_os = "windows") {
                cwd.join(".venv").join("Scripts").join("python.exe")
            } else {
                cwd.join(".venv").join("bin").join("python3")
            };
            let python_str = python.to_string_lossy().to_string();
            let sidecar_for_spawn = Arc::clone(&sidecar_for_setup);

            log::info!("Sidecar Python: {} (cwd: {})", python_str, cwd.display());
            match sidecar_for_spawn.spawn(
                &python_str,
                "backend.sidecar_entry",
                Some(&cwd),
            ) {
                Ok(()) => {
                    log::info!("Sidecar spawned successfully");
                    start_health_check(
                        sidecar_for_spawn,
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
