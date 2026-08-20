// @ts-ignore - @tauri-apps/api provided by Tauri runtime, may be absent in browser tsc
import { listen } from "@tauri-apps/api/event";
import { startRecording as invokeStart, stopRecording as invokeStop } from "../commands";

let isRecording = $state(false);
let elapsedSeconds = $state(0);
let currentText = $state("");
let status = $state<"idle" | "recording" | "processing" | "error">("idle");

// Single Owner: elapsedSeconds is driven ONLY by Rust overlay:tick, never by Svelte setInterval.
// This guarantees one tick source (OverlayState::start_timer) -> 00:01 -> 00:02 ...
let _tickUnlisten: (() => void) | null = null;
let _tickListenerReady = false;

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

// Eagerly attach tick listener (single owner); fire-and-forget
void ensureTickListener();

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
    const response = await invokeStart();
    if (response.status === "ok") {
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
    const response = await invokeStop();
    if (response.status === "ok") {
      status = "idle";
      if (response.data && typeof response.data === "object") {
        const data = response.data as Record<string, unknown>;
        const textVal =
          (typeof data.text === "string" ? data.text : null) ??
          (typeof data.transcription === "string" ? (data.transcription as string) : null) ??
          (data.data && typeof (data.data as Record<string, unknown>).text === "string"
            ? ((data.data as Record<string, unknown>).text as string)
            : null);
        if (typeof textVal === "string" && textVal.trim().length > 0) {
          currentText = textVal;
        } else if (typeof textVal === "string" && textVal.length === 0) {
          currentText = "";
        }
      }
    } else {
      status = "error";
      if (response.error) {
        console.error("stopRecording error:", response.error);
      }
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
}
