import { startRecording as invokeStart, stopRecording as invokeStop } from "../commands";

let isRecording = $state(false);
let elapsedSeconds = $state(0);
let currentText = $state("");
let status = $state<"idle" | "recording" | "processing" | "error">("idle");

let _timerInterval: ReturnType<typeof setInterval> | null = null;

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
    const response = await invokeStart();
    if (response.status === "ok") {
      isRecording = true;
      status = "recording";
      elapsedSeconds = 0;
      currentText = "";
      _timerInterval = setInterval(() => { elapsedSeconds++; }, 1000);
    } else {
      status = "error";
    }
  } catch {
    status = "error";
  }
}

export async function stopRecording(): Promise<void> {
  stopTimer();
  status = "processing";
  try {
    const response = await invokeStop();
    if (response.status === "ok") {
      status = "idle";
      if (response.data && typeof response.data === "object") {
        const data = response.data as Record<string, unknown>;
        // Backend returns data.text (primary) — also handle fallback keys
        const textVal =
          (typeof data.text === "string" ? data.text : null) ??
          (typeof data.transcription === "string" ? (data.transcription as string) : null) ??
          (data.data && typeof (data.data as Record<string, unknown>).text === "string"
            ? ((data.data as Record<string, unknown>).text as string)
            : null);
        if (typeof textVal === "string" && textVal.trim().length > 0) {
          currentText = textVal;
        } else if (typeof textVal === "string" && textVal.length === 0) {
          // Empty string is valid but indicates upstream bug — keep error visibility
          currentText = "";
        }
      }
    } else {
      status = "error";
      // Preserve any error message for debugging
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
  stopTimer();
  isRecording = false;
  elapsedSeconds = 0;
  currentText = "";
  status = "idle";
}

function stopTimer(): void {
  if (_timerInterval !== null) {
    clearInterval(_timerInterval);
    _timerInterval = null;
  }
}
