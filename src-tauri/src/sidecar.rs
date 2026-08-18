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
    #[serde(rename = "register_hotkey")]
    RegisterHotkey { hotkey: String },
    #[serde(rename = "clear_audio")]
    ClearAudio,
    #[serde(rename = "clear_transcriptions")]
    ClearTranscriptions,
    #[serde(rename = "get_status")]
    GetStatus,
}

/// Shared sidecar state managed by Tauri.
pub struct SidecarState {
    inner: Arc<Mutex<SidecarInner>>,
}

struct SidecarInner {
    child: Option<Child>,
    started_at: Instant,
    restart_count: u32,
    is_recording: bool,
    last_stderr: String,
    python_path: String,
    working_dir: Option<std::path::PathBuf>,
}

impl SidecarState {
    pub fn new() -> Self {
        Self {
            inner: Arc::new(Mutex::new(SidecarInner {
                child: None,
                started_at: Instant::now(),
                restart_count: 0,
                is_recording: false,
                last_stderr: String::new(),
                python_path: String::new(),
                working_dir: None,
            })),
        }
    }

    /// Spawn the sidecar Python process with an optional working directory.
    pub fn spawn(
        &self,
        python_path: &str,
        entry_module: &str,
        working_dir: Option<&std::path::Path>,
    ) -> Result<(), String> {
        let mut inner = self.inner.lock().map_err(|e| e.to_string())?;

        // Kill existing sidecar if any
        if let Some(ref mut child) = inner.child {
            let _ = child.kill();
            let _ = child.wait();
        }

        let mut cmd = Command::new(python_path);
        cmd.args(["-m", entry_module])
            .stdin(Stdio::piped())
            .stdout(Stdio::piped())
            .stderr(Stdio::piped());

        if let Some(dir) = working_dir {
            cmd.current_dir(dir);
            log::info!("Sidecar working dir: {}", dir.display());
        }

        let mut child = cmd
            .spawn()
            .map_err(|e| format!("Failed to spawn sidecar: {}", e))?;

        // Drain stderr in a background thread so it doesn't block
        if let Some(stderr) = child.stderr.take() {
            let stderr_inner = self.inner.clone();
            std::thread::spawn(move || {
                let mut reader = BufReader::new(stderr);
                let mut buf = String::new();
                loop {
                    buf.clear();
                    match reader.read_line(&mut buf) {
                        Ok(0) => break, // EOF
                        Ok(_) => {
                            log::error!("[sidecar stderr] {}", buf.trim_end());
                            if let Ok(mut lock) = stderr_inner.lock() {
                                lock.last_stderr.push_str(&buf);
                                // Keep only last 8KB
                                let len = lock.last_stderr.len();
                                if len > 8192 {
                                    lock.last_stderr = lock.last_stderr[len - 4096..].to_string();
                                }
                            }
                        }
                        Err(_) => break,
                    }
                }
            });
        }

        inner.child = Some(child);
        inner.started_at = Instant::now();
        inner.restart_count += 1;
        inner.last_stderr.clear();
        inner.python_path = python_path.to_string();
        inner.working_dir = working_dir.map(|d| d.to_path_buf());

        log::info!(
            "Sidecar spawned (restart #{})",
            inner.restart_count
        );
        Ok(())
    }

    /// Read the last N bytes of stderr output for diagnostics.
    pub fn read_stderr(&self, max_bytes: usize) -> String {
        self.inner
            .lock()
            .map(|i| {
                let s = &i.last_stderr;
                if s.len() <= max_bytes {
                    s.clone()
                } else {
                    s[s.len() - max_bytes..].to_string()
                }
            })
            .unwrap_or_default()
    }

    /// Send a command and read a single-line JSON response.
    ///
    /// This locks, takes ownership of stdin/stdout, does I/O, then returns them.
    /// Handles are ALWAYS returned to the child, even on error.
    pub fn send_command(&self, cmd: &SidecarCommand) -> Result<SidecarResponse, String> {
        let mut inner = self.inner.lock().map_err(|e| e.to_string())?;

        let child = inner.child.as_mut().ok_or("Sidecar not running")?;

        let mut stdin = child.stdin.take().ok_or("No stdin handle")?;
        let mut stdout = child.stdout.take().ok_or("No stdout handle")?;

        // Write command
        let write_result = (|| {
            let payload = serde_json::to_string(cmd).map_err(|e| e.to_string())?;
            stdin
                .write_all(payload.as_bytes())
                .map_err(|e| format!("Write failed: {}", e))?;
            stdin
                .write_all(b"\n")
                .map_err(|e| format!("Write newline failed: {}", e))?;
            stdin
                .flush()
                .map_err(|e| format!("Flush failed: {}", e))?;
            Ok::<(), String>(())
        })();

        if let Err(e) = write_result {
            child.stdin = Some(stdin);
            child.stdout = Some(stdout);
            return Err(e);
        }

        // Read response — borrow stdout temporarily, then drop the reader
        let line = {
            let mut reader = BufReader::new(&mut stdout);
            let mut line = String::new();
            reader
                .read_line(&mut line)
                .map_err(|e| format!("Read failed: {}", e))?;
            line
        }; // reader dropped here, borrow on stdout ends

        // Return handles
        child.stdin = Some(stdin);
        child.stdout = Some(stdout);

        if line.is_empty() {
            return Err("Sidecar closed stdout".into());
        }

        serde_json::from_str(&line).map_err(|e| format!("Invalid JSON from sidecar: {}", e))
    }

    /// Check if the sidecar process is alive.
    pub fn is_alive(&self) -> bool {
        let mut inner = match self.inner.lock() {
            Ok(i) => i,
            Err(_) => return false,
        };
        if let Some(ref mut child) = inner.child {
            match child.try_wait() {
                Ok(Some(_status)) => {
                    // Process has exited
                    inner.child = None;
                    false
                }
                Ok(None) => true,  // Still running
                Err(_) => {
                    inner.child = None;
                    false
                }
            }
        } else {
            false
        }
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

    /// Check if recording is active.
    pub fn is_recording(&self) -> bool {
        self.inner
            .lock()
            .map(|i| i.is_recording)
            .unwrap_or(false)
    }

    /// Set recording state.
    pub fn set_recording(&self, recording: bool) {
        if let Ok(mut inner) = self.inner.lock() {
            inner.is_recording = recording;
        }
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

                // Attempt restart using the same Python path that was originally spawned
                let (python, working_dir) = {
                    let inner = match state.inner.lock() {
                        Ok(i) => i,
                        Err(_) => continue,
                    };
                    (inner.python_path.clone(), inner.working_dir.clone())
                };
                if python.is_empty() {
                    log::error!("Cannot restart sidecar: no python path stored");
                    continue;
                }
                if let Err(e) = state.spawn(&python, "backend.sidecar_entry", working_dir.as_deref()) {
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
    fn test_sidecar_command_clear_audio() {
        let cmd = SidecarCommand::ClearAudio;
        let json = serde_json::to_string(&cmd).unwrap();
        assert_eq!(json, r#"{"command":"clear_audio"}"#);
    }

    #[test]
    fn test_sidecar_command_clear_transcriptions() {
        let cmd = SidecarCommand::ClearTranscriptions;
        let json = serde_json::to_string(&cmd).unwrap();
        assert_eq!(json, r#"{"command":"clear_transcriptions"}"#);
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
