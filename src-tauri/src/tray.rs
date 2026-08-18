use std::sync::Arc;
use tauri::menu::{MenuBuilder, MenuItemBuilder};
use tauri::tray::{TrayIconBuilder, TrayIconEvent};
use tauri::Manager;

use crate::sidecar::SidecarState;

/// Create the system tray with Start/Stop Recording, Show/Hide Window, and Quit.
pub fn create_system_tray(app: &tauri::App, sidecar: Arc<SidecarState>) -> Result<(), String> {
    let start_stop = MenuItemBuilder::with_id("start-stop", "Start Recording")
        .build(app)
        .map_err(|e| e.to_string())?;

    let show_hide = MenuItemBuilder::with_id("show-hide", "Show Window")
        .build(app)
        .map_err(|e| e.to_string())?;

    let quit = MenuItemBuilder::with_id("quit", "Quit")
        .build(app)
        .map_err(|e| e.to_string())?;

    let menu = MenuBuilder::new(app)
        .item(&start_stop)
        .separator()
        .item(&show_hide)
        .separator()
        .item(&quit)
        .build()
        .map_err(|e| e.to_string())?;

    let start_stop_clone = start_stop.clone();
    let sidecar_clone = sidecar.clone();

    let _tray = TrayIconBuilder::new()
        .icon(app.default_window_icon().unwrap().clone())
        .menu(&menu)
        .tooltip("Audio2Text")
        .on_menu_event(move |app, event| match event.id().as_ref() {
            "start-stop" => {
                let was_recording = sidecar_clone.is_recording();
                let cmd = if was_recording {
                    crate::sidecar::SidecarCommand::StopRecording
                } else {
                    crate::sidecar::SidecarCommand::StartRecording
                };
                match sidecar_clone.send_command(&cmd) {
                    Ok(_) => {
                        sidecar_clone.set_recording(!was_recording);
                        let label = if was_recording {
                            "Start Recording"
                        } else {
                            "Stop Recording"
                        };
                        let _ = start_stop_clone.set_text(label);
                    }
                    Err(e) => log::error!("Tray: failed to toggle recording: {}", e),
                }
            }
            "show-hide" => {
                if let Some(window) = app.get_webview_window("main") {
                    if window.is_visible().unwrap_or(false) {
                        let _ = window.hide();
                    } else {
                        let _ = window.show();
                        let _ = window.set_focus();
                    }
                }
            }
            "quit" => {
                app.exit(0);
            }
            _ => {}
        })
        .on_tray_icon_event(|tray, event| {
            if let TrayIconEvent::Click {
                button,
                button_state: _,
                id: _,
                position: _,
                rect: _,
            } = event
            {
                if button == tauri::tray::MouseButton::Left {
                    let app = tray.app_handle();
                    if let Some(window) = app.get_webview_window("main") {
                        if window.is_visible().unwrap_or(false) {
                            let _ = window.hide();
                        } else {
                            let _ = window.show();
                            let _ = window.set_focus();
                        }
                    }
                }
            }
        })
        .build(app)
        .map_err(|e| e.to_string())?;

    log::info!("System tray created");
    Ok(())
}

#[cfg(test)]
mod tests {
    // Tray tests require a running Tauri app context.
    // Verified manually: tray icon visible, menu actions fire.
}
