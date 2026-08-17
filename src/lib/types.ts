/** IPC command types — sent from Tauri frontend to sidecar. */

export interface StartRecordingCmd {
  command: "start_recording";
}

export interface StopRecordingCmd {
  command: "stop_recording";
}

export interface GetConfigCmd {
  command: "get_config";
}

export interface SaveConfigCmd {
  command: "save_config";
  data: Record<string, unknown>;
}

export interface GetHistoryCmd {
  command: "get_history";
}

export type IpcCommand =
  | StartRecordingCmd
  | StopRecordingCmd
  | GetConfigCmd
  | SaveConfigCmd
  | GetHistoryCmd;

/** IPC event types — emitted from sidecar to Tauri frontend. */

export interface TranscriptionReadyEvent {
  event: "transcription_ready";
  data: {
    operation_id: string;
    text: string;
    duration: number;
    language: string;
  };
}

export interface RecordingStartedEvent {
  event: "recording_started";
  data: {
    timestamp: number;
  };
}

export interface RecordingStoppedEvent {
  event: "recording_stopped";
  data: {
    timestamp: number;
    duration: number;
  };
}

export interface StatusUpdateEvent {
  event: "status_update";
  data: {
    message: string;
    color: string;
  };
}

export interface HealthCheckEvent {
  event: "health_check";
  data: {
    alive: boolean;
    uptime: number;
  };
}

export type IpcEvent =
  | TranscriptionReadyEvent
  | RecordingStartedEvent
  | RecordingStoppedEvent
  | StatusUpdateEvent
  | HealthCheckEvent;

/** Command response envelope. */

export interface CommandResponse<T = unknown> {
  status: "ok" | "error";
  data?: T;
  error?: string;
}
