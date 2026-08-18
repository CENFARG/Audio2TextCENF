use arboard::Clipboard;
use enigo::{Direction, Enigo, Key, Keyboard, Settings};

/// Copy text to clipboard and simulate Ctrl+V paste into the active window.
pub fn auto_paste(text: &str) -> Result<(), String> {
    // 1. Copy to system clipboard
    {
        let mut clipboard =
            Clipboard::new().map_err(|e| format!("Failed to open clipboard: {}", e))?;
        clipboard
            .set_text(text)
            .map_err(|e| format!("Failed to set clipboard text: {}", e))?;
    }

    // 2. Brief delay for clipboard to settle
    std::thread::sleep(std::time::Duration::from_millis(50));

    // 3. Simulate Ctrl+V via enigo
    let mut enigo =
        Enigo::new(&Settings::default()).map_err(|e| format!("Failed to init enigo: {}", e))?;

    enigo
        .key(Key::Control, Direction::Press)
        .map_err(|e| format!("Failed to press Ctrl: {}", e))?;
    enigo
        .key(Key::Unicode('v'), Direction::Click)
        .map_err(|e| format!("Failed to press V: {}", e))?;
    enigo
        .key(Key::Control, Direction::Release)
        .map_err(|e| format!("Failed to release Ctrl: {}", e))?;

    Ok(())
}

/// Tauri command: copy transcription text to clipboard and auto-paste.
#[tauri::command]
pub fn auto_paste_command(text: String) -> Result<super::commands::CommandResult, String> {
    auto_paste(&text)?;
    Ok(super::commands::CommandResult {
        status: "ok".into(),
        data: Some(serde_json::json!({ "pasted": true })),
        error: None,
    })
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_auto_paste_empty_string() {
        // Empty string should still attempt clipboard write + paste
        // In CI this may fail due to no display server; verify no panic
        let _ = auto_paste("");
    }

    #[test]
    fn test_auto_paste_ascii_text() {
        let _ = auto_paste("Hello, World!");
    }
}
