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
        if (typeof data.text === "string") {
          currentText = data.text;
        }
      }
    } else {
      status = "error";
    }
    isRecording = false;
  } catch {
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
