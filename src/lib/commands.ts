import { invoke } from "@tauri-apps/api/core";
import type { CommandResponse } from "./types";

export async function startRecording(): Promise<CommandResponse> {
  return invoke<CommandResponse>("start_recording");
}

export async function stopRecording(): Promise<CommandResponse> {
  return invoke<CommandResponse>("stop_recording");
}

export async function getConfig(): Promise<CommandResponse> {
  return invoke<CommandResponse>("get_config");
}

export async function saveConfig(
  config: Record<string, unknown>,
): Promise<CommandResponse> {
  return invoke<CommandResponse>("save_config", { config });
}

export async function getHistory(): Promise<CommandResponse> {
  return invoke<CommandResponse>("get_history");
}
