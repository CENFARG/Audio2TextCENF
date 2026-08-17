use crate::sidecar::{SidecarCommand, SidecarResponse, SidecarState};
use serde::Serialize;
use tauri::State;

/// Generic Tauri command response.
#[derive(Debug, Serialize)]
pub struct CommandResult {
    pub status: String,
    pub data: Option<serde_json::Value>,
    pub error: Option<String>,
}

impl From<Result<SidecarResponse, String>> for CommandResult {
    fn from(result: Result<SidecarResponse, String>) -> Self {
        match result {
            Ok(resp) => CommandResult {
                status: resp.status,
                data: resp.data,
                error: resp.error,
            },
            Err(e) => CommandResult {
                status: "error".into(),
                data: None,
                error: Some(e),
            },
        }
    }
}

/// Start audio recording via the sidecar.
#[tauri::command]
pub async fn start_recording(state: State<'_, SidecarState>) -> Result<CommandResult, String> {
    Ok(CommandResult::from(
        state.send_command(&SidecarCommand::StartRecording),
    ))
}

/// Stop audio recording via the sidecar.
#[tauri::command]
pub async fn stop_recording(state: State<'_, SidecarState>) -> Result<CommandResult, String> {
    Ok(CommandResult::from(
        state.send_command(&SidecarCommand::StopRecording),
    ))
}

/// Get current configuration from the sidecar.
#[tauri::command]
pub async fn get_config(state: State<'_, SidecarState>) -> Result<CommandResult, String> {
    Ok(CommandResult::from(
        state.send_command(&SidecarCommand::GetConfig),
    ))
}

/// Save configuration via the sidecar.
#[tauri::command]
pub async fn save_config(
    state: State<'_, SidecarState>,
    config: serde_json::Value,
) -> Result<CommandResult, String> {
    Ok(CommandResult::from(
        state.send_command(&SidecarCommand::SaveConfig { data: config }),
    ))
}

/// Get transcription history from the sidecar.
#[tauri::command]
pub async fn get_history(state: State<'_, SidecarState>) -> Result<CommandResult, String> {
    Ok(CommandResult::from(
        state.send_command(&SidecarCommand::GetHistory),
    ))
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_command_result_from_ok_response() {
        let resp = SidecarResponse {
            status: "ok".into(),
            data: Some(serde_json::json!({"hotkey": "f9"})),
            error: None,
        };
        let result = CommandResult::from(Ok(resp));
        assert_eq!(result.status, "ok");
        assert!(result.data.is_some());
        assert!(result.error.is_none());
    }

    #[test]
    fn test_command_result_from_error_string() {
        let result = CommandResult::from(Err("something failed".into()));
        assert_eq!(result.status, "error");
        assert!(result.data.is_none());
        assert_eq!(result.error.unwrap(), "something failed");
    }

    #[test]
    fn test_command_result_from_error_response() {
        let resp = SidecarResponse {
            status: "error".into(),
            data: None,
            error: Some("Unknown command".into()),
        };
        let result = CommandResult::from(Ok(resp));
        assert_eq!(result.status, "error");
        assert_eq!(result.error.unwrap(), "Unknown command");
    }

    #[test]
    fn test_command_result_json_serializable() {
        let result = CommandResult {
            status: "ok".into(),
            data: Some(serde_json::json!({"key": "value"})),
            error: None,
        };
        let json = serde_json::to_string(&result).unwrap();
        assert!(json.contains("ok"));
        assert!(json.contains("value"));
    }
}
