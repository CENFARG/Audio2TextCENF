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
  return mod.invoke("start_backend");
}

export async function stopRecording(): Promise<StopResponse> {
  // @ts-ignore - Tauri invoke available at runtime
  const mod: any = await import("@tauri-apps/api/core");
  return mod.invoke("stop_backend");
}
