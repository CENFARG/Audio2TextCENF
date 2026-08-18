use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::Arc;
use std::time::{Duration, Instant};
use tauri::Emitter;
use tauri::Manager;

/// Overlay state: tracks whether recording is active and the start time.
pub struct OverlayState {
    is_active: AtomicBool,
    started_at: std::sync::Mutex<Option<Instant>>,
}

impl OverlayState {
    pub fn new() -> Self {
        Self {
            is_active: AtomicBool::new(false),
            started_at: std::sync::Mutex::new(None),
        }
    }

    pub fn is_active(&self) -> bool {
        self.is_active.load(Ordering::Relaxed)
    }

    pub fn start(&self) {
        self.is_active.store(true, Ordering::Relaxed);
        *self.started_at.lock().unwrap() = Some(Instant::now());
    }

    pub fn stop(&self) {
        self.is_active.store(false, Ordering::Relaxed);
        *self.started_at.lock().unwrap() = None;
    }

    pub fn elapsed_secs(&self) -> u64 {
        self.started_at
            .lock()
            .unwrap()
            .map(|t| t.elapsed().as_secs())
            .unwrap_or(0)
    }
}

/// Show the overlay window.
pub fn show_overlay(app: &tauri::AppHandle) -> Result<(), String> {
    let window = app
        .get_webview_window("overlay")
        .ok_or("Overlay window not found")?;
    window.show().map_err(|e| e.to_string())?;
    Ok(())
}

/// Hide the overlay window.
pub fn hide_overlay(app: &tauri::AppHandle) -> Result<(), String> {
    let window = app
        .get_webview_window("overlay")
        .ok_or("Overlay window not found")?;
    window.hide().map_err(|e| e.to_string())?;
    Ok(())
}

/// Start the overlay timer: emits `overlay:tick` events every second.
pub fn start_timer(app: tauri::AppHandle, overlay: Arc<OverlayState>) {
    tauri::async_runtime::spawn(async move {
        let mut interval = tokio::time::interval(Duration::from_secs(1));
        // Skip the first immediate tick
        interval.tick().await;
        loop {
            interval.tick().await;
            if !overlay.is_active() {
                break;
            }
            let elapsed = overlay.elapsed_secs();
            let time = format!("{:02}:{:02}", elapsed / 60, elapsed % 60);
            let _ = app.emit("overlay:tick", serde_json::json!({ "time": time }));
        }
    });
}

/// Create the overlay window during app setup. Returns the window handle.
pub fn create_overlay_window(app: &tauri::App) -> Result<(), String> {
    let overlay_url = tauri::WebviewUrl::App("overlay.html".into());

    let _overlay = tauri::WebviewWindowBuilder::new(app, "overlay", overlay_url)
        .title("")
        .inner_size(220.0, 52.0)
        .decorations(false)
        .always_on_top(true)
        .skip_taskbar(true)
        .visible(false)
        .position(100.0, 100.0)
        .build()
        .map_err(|e| format!("Failed to create overlay window: {}", e))?;

    log::info!("Overlay window created (hidden)");
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_overlay_state_new() {
        let state = OverlayState::new();
        assert!(!state.is_active());
        assert_eq!(state.elapsed_secs(), 0);
    }

    #[test]
    fn test_overlay_state_start_stop() {
        let state = OverlayState::new();
        state.start();
        assert!(state.is_active());

        std::thread::sleep(Duration::from_millis(1100));
        assert!(state.elapsed_secs() >= 1);

        state.stop();
        assert!(!state.is_active());
        assert_eq!(state.elapsed_secs(), 0);
    }
}
