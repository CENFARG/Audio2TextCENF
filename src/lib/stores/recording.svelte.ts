import { listen, type UnlistenFn } from "@tauri-apps/api/event";
import { startRecording as invokeStart, stopRecording as invokeStop } from "../commands";

let isRecording = $state(false);
let elapsedSeconds = $state(0);
let currentText = $state("");
let status = $state<"idle" | "recording" | "processing" | "error">("idle");

let _unlistenTick: UnlistenFn | null = null;

function parseTimeToSeconds(time: string): number {
  const parts = time.split(":").map(Number);
  if (parts.length === 2) return parts[0] * 60 + parts[1];
  return 0;
}

async function attachTickListener(): Promise<void> {
  if (_unlistenTick) return;
  _unlistenTick = await listen<{ time: string } | number>("overlay:tick", (event) => {
    const payload = event.payload as unknown;
    if (typeof payload === "string") {
      elapsedSeconds = parseTimeToSeconds(payload);
    } else if (typeof payload === "number") {
      elapsedSeconds = payload;
    } else if (payload && typeof payload === "object" && "time" in (payload as Record<string, unknown>)) {
      elapsedSeconds = parseTimeToSeconds((payload as { time: string }).time);
    }
  });
}

function detachTickListener(): void {
  if (_unlistenTick) {
    _unlistenTick();
    _unlistenTick = null;
  }
}

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
  isRecording = true;
  elapsedSeconds = 0;
  status = "recording";
  currentText = "";
  await attachTickListener();
  try {
    const response = await invokeStart();
    if (response.status !== "ok") {
      detachTickListener();
      isRecording = false;
      status = "error";
    }
  } catch {
    detachTickListener();
    isRecording = false;
    status = "error";
  }
}

export async function stopRecording(): Promise<void> {
  detachTickListener();
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
  detachTickListener();
  isRecording = false;
  elapsedSeconds = 0;
  currentText = "";
  status = "idle";
}
