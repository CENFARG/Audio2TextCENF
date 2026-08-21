import { listen } from "@tauri-apps/api/event";
import { APIClient } from "../infrastructure/api-client";

const api = new APIClient();

let isRecording = $state(false);
let elapsedSeconds = $state(0);
let currentText = $state("");
let status = $state<"idle" | "recording" | "processing" | "error">("idle");

// Single Owner: elapsedSeconds is driven ONLY by Rust overlay:tick, never by Svelte setInterval.
// This guarantees one tick source (OverlayState::start_timer) -> 00:01 -> 00:02 ...
let _tickUnlisten: (() => void) | null = null;
let _tickListenerReady = false;
let _hotkeyUnlisten: (() => void) | null = null;
let _trayUnlisten: (() => void) | null = null;
let _hotkeyErrorUnlisten: (() => void) | null = null;
let _startedUnlisten: (() => void) | null = null;
let _stoppedUnlisten: (() => void) | null = null;
let _hotkeyListenerReady = false;

async function ensureTickListener(): Promise<void> {
  if (_tickListenerReady) return;
  _tickListenerReady = true;
  try {
    _tickUnlisten = await listen<{ time: string }>("overlay:tick", (event: { payload: { time: string } }) => {
      const timeStr = event.payload?.time ?? "00:00";
      const [m, s] = timeStr.split(":").map(Number);
      if (!Number.isNaN(m) && !Number.isNaN(s)) {
        elapsedSeconds = m * 60 + s;
      }
    });
  } catch {
    // Non-Tauri env (browser dev) — keep elapsedSeconds at 0, no crash
  }
}

async function ensureHotkeyListener(): Promise<void> {
  if (_hotkeyListenerReady) return;
  _hotkeyListenerReady = true;
  try {
    // Single Owner bridge: hotkey:toggle_recording -> start/stop via FastAPI (single owner)
    _hotkeyUnlisten = await listen("hotkey:toggle_recording", async () => {
      try {
        if (isRecording) await stopRecording();
        else await startRecording();
      } catch (e) {
        console.error("[recording] hotkey handler error", e);
      }
    });
    _trayUnlisten = await listen("tray:toggle_recording", async () => {
      try {
        if (isRecording) await stopRecording();
        else await startRecording();
      } catch (e) {
        console.error("[recording] tray handler error", e);
      }
    });
    _hotkeyErrorUnlisten = await listen("hotkey:error", (e: any) => {
      console.warn("[recording] hotkey:error", e.payload);
    });
    _startedUnlisten = await listen("recording:started", () => {
      isRecording = true;
      status = "recording";
      elapsedSeconds = 0;
      currentText = "";
    });
    _stoppedUnlisten = await listen("recording:stopped", () => {
      isRecording = false;
      // status will be set to idle/processing by stopRecording; ensure idle if still recording
      if (status === "recording") status = "idle";
    });
  } catch {
    // Non-Tauri env
  }
}

// Eagerly attach listeners (single owner); fire-and-forget
void ensureTickListener();
void ensureHotkeyListener();

export function getRecordingState() {
  return {
    get isRecording() {
      return isRecording;
    },
    get elapsedSeconds() {
      return elapsedSeconds;
    },
    get currentText() {
      return currentText;
    },
    get status() {
      return status;
    },
  };
}

export async function startRecording(): Promise<void> {
  try {
    await ensureTickListener();
    await ensureHotkeyListener();
    const response = await api.startRecording();
    if (response.status === "recording" || response.session_id || response.status === "ok") {
      isRecording = true;
      status = "recording";
      elapsedSeconds = 0;
      currentText = "";
    } else {
      status = "error";
    }
  } catch {
    status = "error";
  }
}

export async function stopRecording(): Promise<void> {
  status = "processing";
  try {
    const response = await api.stopRecording();
    // FastAPI /transcribe/stop returns {session_id, status, text, transcription?}
    const textVal =
      (typeof response.text === "string" ? response.text : null) ??
      (typeof response.transcription === "string" ? (response.transcription as string) : null) ??
      (response.data && typeof (response.data as Record<string, unknown>).text === "string"
        ? ((response.data as Record<string, unknown>).text as string)
        : null);
    if (typeof textVal === "string" && textVal.trim().length > 0) {
      currentText = textVal;
      status = "idle";
    } else if (response.error) {
      status = "error";
      console.error("stopRecording error:", response.error);
    } else {
      // Empty text — treat as error (Single Owner: never ok with "")
      status = "error";
      console.warn("stopRecording returned empty text", response);
    }
    isRecording = false;
  } catch (e) {
    console.error("stopRecording exception:", e);
    status = "error";
    isRecording = false;
  }
}

export function resetRecording(): void {
  isRecording = false;
  elapsedSeconds = 0;
  currentText = "";
  status = "idle";
}

export function _disposeTickListener(): void {
  if (_tickUnlisten) {
    _tickUnlisten();
    _tickUnlisten = null;
    _tickListenerReady = false;
  }
  if (_hotkeyUnlisten) {
    _hotkeyUnlisten();
    _hotkeyUnlisten = null;
  }
  if (_trayUnlisten) {
    _trayUnlisten();
    _trayUnlisten = null;
  }
  if (_hotkeyErrorUnlisten) {
    _hotkeyErrorUnlisten();
    _hotkeyErrorUnlisten = null;
  }
  if (_startedUnlisten) {
    _startedUnlisten();
    _startedUnlisten = null;
  }
  if (_stoppedUnlisten) {
    _stoppedUnlisten();
    _stoppedUnlisten = null;
  }
  _hotkeyListenerReady = false;
  if (_tickUnlisten) {
    _tickUnlisten();
    _tickUnlisten = null;
    _tickListenerReady = false;
  }
}

// Alias for full dispose (all listeners)
export const disposeRecordingListeners = _disposeTickListener;
