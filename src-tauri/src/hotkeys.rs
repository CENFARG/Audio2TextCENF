use std::sync::Arc;
use tauri::Emitter;
use tauri_plugin_global_shortcut::{Code, GlobalShortcutExt, Modifiers, Shortcut, ShortcutState};

use crate::sidecar::{SidecarCommand, SidecarState};

/// Parse a hotkey string like "Ctrl+Alt+F9" into Tauri modifiers and code.
///
/// Supported modifiers: Ctrl/Control, Alt, Shift, Super/Meta/Win/Cmd
/// Supported keys: F1-F24, a-z, 0-9, Space, Enter, Tab, Escape, arrows, etc.
pub fn parse_shortcut_string(s: &str) -> Result<(Modifiers, Code), String> {
    let parts: Vec<String> = s.split('+').map(|p| p.trim().to_lowercase()).collect();
    if parts.is_empty() || s.trim().is_empty() {
        return Err("Empty shortcut string".into());
    }

    let key_str = parts.last().ok_or("No key specified")?;
    let mut modifiers = Modifiers::empty();

    for part in &parts[..parts.len() - 1] {
        match part.as_str() {
            "ctrl" | "control" => modifiers |= Modifiers::CONTROL,
            "alt" => modifiers |= Modifiers::ALT,
            "shift" => modifiers |= Modifiers::SHIFT,
            "super" | "meta" | "win" | "cmd" => modifiers |= Modifiers::SUPER,
            _ => return Err(format!("Unknown modifier: {}", part)),
        }
    }

    let code = parse_key_code(key_str)?;
    Ok((modifiers, code))
}

fn parse_key_code(s: &str) -> Result<Code, String> {
    match s {
        "f1" => Ok(Code::F1),
        "f2" => Ok(Code::F2),
        "f3" => Ok(Code::F3),
        "f4" => Ok(Code::F4),
        "f5" => Ok(Code::F5),
        "f6" => Ok(Code::F6),
        "f7" => Ok(Code::F7),
        "f8" => Ok(Code::F8),
        "f9" => Ok(Code::F9),
        "f10" => Ok(Code::F10),
        "f11" => Ok(Code::F11),
        "f12" => Ok(Code::F12),
        "f13" => Ok(Code::F13),
        "f14" => Ok(Code::F14),
        "f15" => Ok(Code::F15),
        "f16" => Ok(Code::F16),
        "f17" => Ok(Code::F17),
        "f18" => Ok(Code::F18),
        "f19" => Ok(Code::F19),
        "f20" => Ok(Code::F20),
        "f21" => Ok(Code::F21),
        "f22" => Ok(Code::F22),
        "f23" => Ok(Code::F23),
        "f24" => Ok(Code::F24),
        "space" => Ok(Code::Space),
        "enter" | "return" => Ok(Code::Enter),
        "tab" => Ok(Code::Tab),
        "backspace" => Ok(Code::Backspace),
        "delete" | "del" => Ok(Code::Delete),
        "escape" | "esc" => Ok(Code::Escape),
        "home" => Ok(Code::Home),
        "end" => Ok(Code::End),
        "pageup" | "pgup" => Ok(Code::PageUp),
        "pagedown" | "pgdn" => Ok(Code::PageDown),
        "arrowup" | "up" => Ok(Code::ArrowUp),
        "arrowdown" | "down" => Ok(Code::ArrowDown),
        "arrowleft" | "left" => Ok(Code::ArrowLeft),
        "arrowright" | "right" => Ok(Code::ArrowRight),
        _ if s.len() == 1 => parse_single_char(s),
        _ => Err(format!("Unknown key: {}", s)),
    }
}

fn parse_single_char(s: &str) -> Result<Code, String> {
    let ch = s.chars().next().unwrap();
    if ch.is_ascii_digit() {
        match ch {
            '0' => Ok(Code::Digit0),
            '1' => Ok(Code::Digit1),
            '2' => Ok(Code::Digit2),
            '3' => Ok(Code::Digit3),
            '4' => Ok(Code::Digit4),
            '5' => Ok(Code::Digit5),
            '6' => Ok(Code::Digit6),
            '7' => Ok(Code::Digit7),
            '8' => Ok(Code::Digit8),
            '9' => Ok(Code::Digit9),
            _ => unreachable!(),
        }
    } else if ch.is_ascii_alphabetic() {
        match ch.to_ascii_lowercase() {
            'a' => Ok(Code::KeyA),
            'b' => Ok(Code::KeyB),
            'c' => Ok(Code::KeyC),
            'd' => Ok(Code::KeyD),
            'e' => Ok(Code::KeyE),
            'f' => Ok(Code::KeyF),
            'g' => Ok(Code::KeyG),
            'h' => Ok(Code::KeyH),
            'i' => Ok(Code::KeyI),
            'j' => Ok(Code::KeyJ),
            'k' => Ok(Code::KeyK),
            'l' => Ok(Code::KeyL),
            'm' => Ok(Code::KeyM),
            'n' => Ok(Code::KeyN),
            'o' => Ok(Code::KeyO),
            'p' => Ok(Code::KeyP),
            'q' => Ok(Code::KeyQ),
            'r' => Ok(Code::KeyR),
            's' => Ok(Code::KeyS),
            't' => Ok(Code::KeyT),
            'u' => Ok(Code::KeyU),
            'v' => Ok(Code::KeyV),
            'w' => Ok(Code::KeyW),
            'x' => Ok(Code::KeyX),
            'y' => Ok(Code::KeyY),
            'z' => Ok(Code::KeyZ),
            _ => unreachable!(),
        }
    } else {
        Err(format!("Unknown key: {}", s))
    }
}

fn toggle_recording(app: &tauri::AppHandle, sidecar: &SidecarState) {
    let cmd = if sidecar.is_recording() {
        sidecar.set_recording(false);
        SidecarCommand::StopRecording
    } else {
        sidecar.set_recording(true);
        SidecarCommand::StartRecording
    };
    match sidecar.send_command(&cmd) {
        Ok(_) => {
            log::info!("Recording toggled via hotkey");
            let event_name = if sidecar.is_recording() {
                "recording:started"
            } else {
                "recording:stopped"
            };
            let _ = app.emit(event_name, ());
        }
        Err(e) => log::error!("Failed to toggle recording: {}", e),
    }
}

/// Register the default global hotkey (Ctrl+Alt+F9) for toggling recording.
pub fn register_default_hotkey(
    app_handle: &tauri::AppHandle,
    sidecar: Arc<SidecarState>,
) -> Result<(), String> {
    let (modifiers, code) = parse_shortcut_string("Ctrl+Alt+F10")?;
    let shortcut = Shortcut::new(Some(modifiers), code);

    let sidecar_clone = sidecar.clone();
    let app_clone = app_handle.clone();
    app_handle
        .global_shortcut()
        .on_shortcut(shortcut, move |_app, _shortcut, event| {
            if event.state == ShortcutState::Pressed {
                toggle_recording(&app_clone, &sidecar_clone);
            }
        })
        .map_err(|e| format!("Failed to register shortcut handler: {}", e))?;

    log::info!("Global hotkey Ctrl+Alt+F10 registered");
    Ok(())
}

/// Register a custom hotkey string via the global shortcut API.
pub fn register_custom_hotkey(
    app_handle: &tauri::AppHandle,
    hotkey_str: &str,
    sidecar: Arc<SidecarState>,
) -> Result<(), String> {
    let (modifiers, code) = parse_shortcut_string(hotkey_str)?;
    let shortcut = Shortcut::new(Some(modifiers), code);

    let sidecar_clone = sidecar.clone();
    let app_clone = app_handle.clone();
    app_handle
        .global_shortcut()
        .on_shortcut(shortcut, move |_app, _shortcut, event| {
            if event.state == ShortcutState::Pressed {
                toggle_recording(&app_clone, &sidecar_clone);
            }
        })
        .map_err(|e| format!("Failed to register shortcut handler: {}", e))?;

    log::info!("Custom hotkey '{}' registered", hotkey_str);
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_parse_ctrl_alt_f9() {
        let (mods, code) = parse_shortcut_string("Ctrl+Alt+F9").unwrap();
        assert!(mods.contains(Modifiers::CONTROL));
        assert!(mods.contains(Modifiers::ALT));
        assert!(!mods.contains(Modifiers::SHIFT));
        assert_eq!(code, Code::F9);
    }

    #[test]
    fn test_parse_ctrl_shift_s() {
        let (mods, code) = parse_shortcut_string("Ctrl+Shift+S").unwrap();
        assert!(mods.contains(Modifiers::CONTROL));
        assert!(mods.contains(Modifiers::SHIFT));
        assert_eq!(code, Code::KeyS);
    }

    #[test]
    fn test_parse_single_key() {
        let (mods, code) = parse_shortcut_string("F12").unwrap();
        assert!(mods.is_empty());
        assert_eq!(code, Code::F12);
    }

    #[test]
    fn test_parse_lower_case() {
        let (mods, code) = parse_shortcut_string("ctrl+alt+f9").unwrap();
        assert!(mods.contains(Modifiers::CONTROL));
        assert!(mods.contains(Modifiers::ALT));
        assert_eq!(code, Code::F9);
    }

    #[test]
    fn test_parse_with_spaces() {
        let (mods, code) = parse_shortcut_string("Ctrl + Alt + F9").unwrap();
        assert!(mods.contains(Modifiers::CONTROL));
        assert!(mods.contains(Modifiers::ALT));
        assert_eq!(code, Code::F9);
    }

    #[test]
    fn test_parse_super_modifier() {
        let (mods, code) = parse_shortcut_string("Super+Ctrl+Space").unwrap();
        assert!(mods.contains(Modifiers::SUPER));
        assert!(mods.contains(Modifiers::CONTROL));
        assert_eq!(code, Code::Space);
    }

    #[test]
    fn test_parse_invalid_modifier() {
        let result = parse_shortcut_string("Bad+F9");
        assert!(result.is_err());
        assert!(result.unwrap_err().contains("Unknown modifier"));
    }

    #[test]
    fn test_parse_invalid_key() {
        let result = parse_shortcut_string("Ctrl+InvalidKey");
        assert!(result.is_err());
        assert!(result.unwrap_err().contains("Unknown key"));
    }

    #[test]
    fn test_parse_empty_string() {
        assert!(parse_shortcut_string("").is_err());
    }

    #[test]
    fn test_parse_whitespace_only() {
        assert!(parse_shortcut_string("   ").is_err());
    }

    #[test]
    fn test_parse_digit_key() {
        let (mods, code) = parse_shortcut_string("Ctrl+5").unwrap();
        assert!(mods.contains(Modifiers::CONTROL));
        assert_eq!(code, Code::Digit5);
    }

    #[test]
    fn test_parse_letter_key() {
        let (mods, code) = parse_shortcut_string("Alt+A").unwrap();
        assert!(mods.contains(Modifiers::ALT));
        assert_eq!(code, Code::KeyA);
    }

    #[test]
    fn test_parse_all_modifiers() {
        let (mods, _) = parse_shortcut_string("Ctrl+Alt+Shift+Super+F1").unwrap();
        assert!(mods.contains(Modifiers::CONTROL));
        assert!(mods.contains(Modifiers::ALT));
        assert!(mods.contains(Modifiers::SHIFT));
        assert!(mods.contains(Modifiers::SUPER));
    }

    #[test]
    fn test_parse_control_alias() {
        let (mods, code) = parse_shortcut_string("Control+F9").unwrap();
        assert!(mods.contains(Modifiers::CONTROL));
        assert_eq!(code, Code::F9);
    }

    #[test]
    fn test_parse_meta_alias() {
        let (mods, code) = parse_shortcut_string("Meta+Ctrl+F9").unwrap();
        assert!(mods.contains(Modifiers::SUPER));
        assert!(mods.contains(Modifiers::CONTROL));
        assert_eq!(code, Code::F9);
    }

    #[test]
    fn test_parse_escape_key() {
        let (_, code) = parse_shortcut_string("Escape").unwrap();
        assert_eq!(code, Code::Escape);
    }

    #[test]
    fn test_parse_enter_key() {
        let (_, code) = parse_shortcut_string("Enter").unwrap();
        assert_eq!(code, Code::Enter);
    }

    #[test]
    fn test_parse_arrow_keys() {
        let (_, code) = parse_shortcut_string("ArrowUp").unwrap();
        assert_eq!(code, Code::ArrowUp);
        let (_, code) = parse_shortcut_string("Left").unwrap();
        assert_eq!(code, Code::ArrowLeft);
    }
}
