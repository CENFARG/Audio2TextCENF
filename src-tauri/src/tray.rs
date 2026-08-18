//! System tray with Start/Stop Recording, Show/Hide Window, and Quit.

use tauri::menu::{MenuBuilder, MenuItemBuilder};
use tauri::tray::{TrayIconBuilder, TrayIconEvent};
use tauri::Emitter;
use tauri::Manager;

/// Tray state: tracks recording status for menu label updates.
pub struct TrayState {
    is_recording: std::sync::atomic::AtomicBool,
}

impl TrayState {
    pub fn new() -> Self {
        Self {
            is_recording: std::sync::atomic::AtomicBool::new(false),
        }
    }

    pub fn is_recording(&self) -> bool {
        self.is_recording
            .load(std::sync::atomic::Ordering::Relaxed)
    }

    pub fn set_recording(&self, recording: bool) {
        self.is_recording
            .store(recording, std::sync::atomic::Ordering::Relaxed);
    }
}

/// Create the system tray with Start/Stop Recording, Show/Hide Window, and Quit.
pub fn create_system_tray(app: &tauri::App) -> Result<(), String> {
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

    let _tray = TrayIconBuilder::new()
        .icon(app.default_window_icon().unwrap().clone())
        .menu(&menu)
        .tooltip("Audio2Text")
        .on_menu_event(move |app, event| match event.id().as_ref() {
            "start-stop" => {
                // Toggle recording via event emission
                let _ = app.emit("tray:toggle_recording", ());
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
    use super::*;

    #[test]
    fn test_tray_state_new() {
        let state = TrayState::new();
        assert!(!state.is_recording());
    }

    #[test]
    fn test_tray_state_recording() {
        let state = TrayState::new();
        state.set_recording(true);
        assert!(state.is_recording());
        state.set_recording(false);
        assert!(!state.is_recording());
    }
}
