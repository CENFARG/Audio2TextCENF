use serde::{Deserialize, Serialize};
use std::io::{BufRead, BufReader, Write};
use std::process::{Child, Command, Stdio};
use std::sync::{Arc, Mutex};
use std::time::{Duration, Instant};
use tauri::Emitter;

/// Response envelope matching the Python sidecar's output format.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SidecarResponse {
    pub status: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub data: Option<serde_json::Value>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub error: Option<String>,
}

/// IPC command sent to the sidecar (matches Python sidecar_entry.py).
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(tag = "command")]
pub enum SidecarCommand {
    #[serde(rename = "start_recording")]
    StartRecording,
    #[serde(rename = "stop_recording")]
    StopRecording,
    #[serde(rename = "get_config")]
    GetConfig,
    #[serde(rename = "save_config")]
    SaveConfig { data: serde_json::Value },
    #[serde(rename = "get_history")]
    GetHistory,
}

/// Shared sidecar state managed by Tauri.
pub struct SidecarState {
    inner: Mutex<SidecarInner>,
}

struct SidecarInner {
    child: Option<Child>,
    started_at: Instant,
    restart_count: u32,
}

impl SidecarState {
    pub fn new() -> Self {
        Self {
            inner: Mutex::new(SidecarInner {
                child: None,
                started_at: Instant::now(),
                restart_count: 0,
            }),
        }
    }

    /// Spawn the sidecar Python process and take control of its stdin/stdout.
    pub fn spawn(&self, python_path: &str, entry_module: &str) -> Result<(), String> {
        let mut inner = self.inner.lock().map_err(|e| e.to_string())?;

        // Kill existing sidecar if any
        if let Some(ref mut child) = inner.child {
            let _ = child.kill();
            let _ = child.wait();
        }

        let child = Command::new(python_path)
            .args(["-m", entry_module])
            .stdin(Stdio::piped())
            .stdout(Stdio::piped())
            .stderr(Stdio::null())
            .spawn()
            .map_err(|e| format!("Failed to spawn sidecar: {}", e))?;

        inner.child = Some(child);
        inner.started_at = Instant::now();
        inner.restart_count += 1;

        log::info!(
            "Sidecar spawned (restart #{})",
            inner.restart_count
        );
        Ok(())
    }

    /// Send a command and read a single-line JSON response.
    ///
    /// This locks, takes ownership of stdin/stdout, does I/O, then returns them.
    pub fn send_command(&self, cmd: &SidecarCommand) -> Result<SidecarResponse, String> {
        let mut inner = self.inner.lock().map_err(|e| e.to_string())?;

        let child = inner.child.as_mut().ok_or("Sidecar not running")?;

        let mut stdin = child.stdin.take().ok_or("No stdin handle")?;
        let stdout = child.stdout.take().ok_or("No stdout handle")?;

        // Write command
        let payload = serde_json::to_string(cmd).map_err(|e| e.to_string())?;
        stdin
            .write_all(payload.as_bytes())
            .map_err(|e| format!("Write failed: {}", e))?;
        stdin
            .write_all(b"\n")
            .map_err(|e| format!("Write newline failed: {}", e))?;
        stdin.flush().map_err(|e| format!("Flush failed: {}", e))?;

        // Read response
        let mut reader = BufReader::new(stdout);
        let mut line = String::new();
        reader
            .read_line(&mut line)
            .map_err(|e| format!("Read failed: {}", e))?;

        // Return stdin/stdout to the child
        child.stdin = Some(stdin);
        child.stdout = Some(reader.into_inner());

        if line.is_empty() {
            return Err("Sidecar closed stdout".into());
        }

        serde_json::from_str(&line).map_err(|e| format!("Invalid JSON from sidecar: {}", e))
    }

    /// Check if the sidecar process is alive.
    pub fn is_alive(&self) -> bool {
        let inner = match self.inner.lock() {
            Ok(i) => i,
            Err(_) => return false,
        };
        inner.child.is_some()
    }

    /// Get uptime in seconds.
    pub fn uptime_secs(&self) -> u64 {
        let inner = match self.inner.lock() {
            Ok(i) => i,
            Err(_) => return 0,
        };
        inner.started_at.elapsed().as_secs()
    }

    /// Kill the sidecar process.
    pub fn kill(&self) -> Result<(), String> {
        let mut inner = self.inner.lock().map_err(|e| e.to_string())?;
        if let Some(ref mut child) = inner.child {
            let _ = child.kill();
            let _ = child.wait();
        }
        inner.child = None;
        Ok(())
    }
}

/// Health check loop: runs every `interval` and emits events.
pub fn start_health_check(
    state: Arc<SidecarState>,
    app_handle: tauri::AppHandle,
    interval: Duration,
) {
    tauri::async_runtime::spawn(async move {
        loop {
            // Use tokio sleep via tauri's async runtime
            tokio::time::sleep(interval).await;

            let alive = state.is_alive();
            let uptime = state.uptime_secs();

            let _ = app_handle.emit(
                "health_check",
                serde_json::json!({
                    "event": "health_check",
                    "data": { "alive": alive, "uptime": uptime }
                }),
            );

            // Auto-restart with exponential backoff on crash
            if !alive {
                let restart_count = {
                    let inner = match state.inner.lock() {
                        Ok(i) => i,
                        Err(_) => continue,
                    };
                    inner.restart_count
                };

                let backoff_ms = 1000 * 2u64.pow(restart_count.min(5));
                log::warn!(
                    "Sidecar dead, restarting in {}ms (attempt {})",
                    backoff_ms,
                    restart_count + 1
                );
                tokio::time::sleep(Duration::from_millis(backoff_ms)).await;

                // Attempt restart
                let python = if cfg!(target_os = "windows") {
                    "python"
                } else {
                    "python3"
                };
                if let Err(e) = state.spawn(python, "backend.sidecar_entry") {
                    log::error!("Sidecar restart failed: {}", e);
                }
            }
        }
    });
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_sidecar_response_roundtrip() {
        let resp = SidecarResponse {
            status: "ok".into(),
            data: Some(serde_json::json!({"hotkey": "f9"})),
            error: None,
        };
        let json = serde_json::to_string(&resp).unwrap();
        let parsed: SidecarResponse = serde_json::from_str(&json).unwrap();
        assert_eq!(parsed.status, "ok");
        assert!(parsed.error.is_none());
    }

    #[test]
    fn test_sidecar_command_serialization() {
        let cmd = SidecarCommand::StartRecording;
        let json = serde_json::to_string(&cmd).unwrap();
        assert_eq!(json, r#"{"command":"start_recording"}"#);
    }

    #[test]
    fn test_sidecar_command_save_config() {
        let cmd = SidecarCommand::SaveConfig {
            data: serde_json::json!({"hotkey": "f9"}),
        };
        let json = serde_json::to_string(&cmd).unwrap();
        let parsed: serde_json::Value = serde_json::from_str(&json).unwrap();
        assert_eq!(parsed["command"], "save_config");
        assert_eq!(parsed["data"]["hotkey"], "f9");
    }

    #[test]
    fn test_sidecar_error_response() {
        let resp = SidecarResponse {
            status: "error".into(),
            data: None,
            error: Some("Unknown command".into()),
        };
        let json = serde_json::to_string(&resp).unwrap();
        let parsed: SidecarResponse = serde_json::from_str(&json).unwrap();
        assert_eq!(parsed.status, "error");
        assert_eq!(parsed.error.unwrap(), "Unknown command");
    }

    #[test]
    fn test_sidecar_state_new() {
        let state = SidecarState::new();
        assert!(!state.is_alive());
        assert_eq!(state.uptime_secs(), 0);
    }
}
