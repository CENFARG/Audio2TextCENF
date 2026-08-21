/** @File: src/lib/commands.ts — Tauri invoke wrappers for Single Owner State Machine */
export interface StartResponse {
  status: string;
  operation_id?: string;
  session_id?: string;
}
export interface StopResponse {
  status: string;
  operation_id?: string;
  data?: unknown;
  error?: unknown;
}

export async function startRecording(): Promise<StartResponse> {
  // @ts-ignore - Tauri invoke available at runtime
  const mod: any = await import("@tauri-apps/api/core");
  const res = await mod.invoke("start_backend");
  if (typeof res === "string") {
    try { return JSON.parse(res); } catch { return { status: res }; }
  }
  return res;
}

export async function stopRecording(): Promise<StopResponse> {
  // @ts-ignore - Tauri invoke available at runtime
  const mod: any = await import("@tauri-apps/api/core");
  const res = await mod.invoke("stop_backend");
  if (typeof res === "string") {
    try { return JSON.parse(res); } catch { return { status: res }; }
  }
  return res;
}

export async function toggleRecording(): Promise<StartResponse> {
  // @ts-ignore - Tauri invoke available at runtime
  const mod: any = await import("@tauri-apps/api/core");
  const res = await mod.invoke("toggle_recording");
  if (typeof res === "string") {
    try { return JSON.parse(res); } catch { return { status: res }; }
  }
  return res;
}

export async function getHotkeys(): Promise<{ record: string; cancel: string; error?: string }> {
  // @ts-ignore - Tauri invoke available at runtime
  const mod: any = await import("@tauri-apps/api/core");
  const res = await mod.invoke("get_hotkeys");
  if (typeof res === "string") {
    try { return JSON.parse(res); } catch { return { record: "F9", cancel: "Escape" }; }
  }
  return res ?? { record: "F9", cancel: "Escape" };
}

export async function setHotkey(name: string, binding: string): Promise<{ record: string; cancel?: string; error?: string }> {
  // @ts-ignore - Tauri invoke available at runtime
  const mod: any = await import("@tauri-apps/api/core");
  const res = await mod.invoke("set_hotkey", { name, binding });
  if (typeof res === "string") {
    try { return JSON.parse(res); } catch { return { record: binding }; }
  }
  return res ?? { record: binding };
}
