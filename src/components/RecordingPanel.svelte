<script lang="ts">
  import { getRecordingState, startRecording, stopRecording } from "../lib/stores/recording.svelte";
  import { invoke } from "@tauri-apps/api/core";
  import { t } from "../lib/i18n.svelte";

  const recState = getRecordingState();

  let audioCount = $state(0);
  let audioSizeMB = $state("0.0");
  let transcriptionCount = $state(0);
  let clearStatus = $state<"idle" | "audio" | "transcriptions">("idle");

  function formatTime(seconds: number): string {
    const m = Math.floor(seconds / 60)
      .toString()
      .padStart(2, "0");
    const s = (seconds % 60).toString().padStart(2, "0");
    return `${m}:${s}`;
  }

  function toggleRecording(): void {
    if (state.isRecording) {
      stopRecording();
    } else {
      startRecording();
    }
  }

  async function loadFileInfo(): Promise<void> {
    try {
      const response = await invoke<{ status: string; data?: Record<string, unknown> }>("get_config");
      if (response.status === "ok" && response.data) {
        // We'll get file info from sidecar if available
        // For now, show placeholder counts
      }
    } catch {
      // ignore
    }
  }

  async function clearAudio(): Promise<void> {
    try {
      await invoke("clear_audio");
      clearStatus = "audio";
      audioCount = 0;
      audioSizeMB = "0.0";
      setTimeout(() => { clearStatus = "idle"; }, 2000);
    } catch {
      // ignore
    }
  }

  async function clearTranscriptions(): Promise<void> {
    try {
      await invoke("clear_transcriptions");
      clearStatus = "transcriptions";
      transcriptionCount = 0;
      setTimeout(() => { clearStatus = "idle"; }, 2000);
    } catch {
      // ignore
    }
  }

  $effect(() => {
    loadFileInfo();
  });
</script>

<div class="recording-panel">
  <div class="mic-indicator" class:active={recState.isRecording}>
    <div class="mic-icon">🎤</div>
    <div class="level-bars">
      {#each Array(8) as _, i}
        <div
          class="bar"
          class:active={recState.isRecording && Math.random() > 0.3}
          style="animation-delay: {i * 0.1}s"
        ></div>
      {/each}
    </div>
  </div>

  <button
    class="record-btn"
    class:recording={recState.isRecording}
    onclick={toggleRecording}
    disabled={recState.status === "processing"}
  >
    {#if recState.status === "processing"}
      {t("status_processing")}
    {:else if recState.isRecording}
      {t("status_recording")}
    {:else}
      {t("status_ready")}
    {/if}
  </button>

  <div class="timer">{formatTime(recState.elapsedSeconds)}</div>

  {#if recState.currentText}
    <div class="transcription-preview">
      <p>{state.currentText}</p>
    </div>
  {/if}

  {#if recState.status === "error"}
    <div class="error-msg">{t("status_error")}</div>
  {/if}

  <div class="file-info">
    <div class="info-row">
      <span class="info-label">{t("audio_info", { size: audioSizeMB, count: audioCount })}</span>
      <span class="info-separator">·</span>
      <span class="info-label">{t("transcriptions_info", { size: "0" })}</span>
    </div>
    <div class="clear-buttons">
      <button class="clear-btn" onclick={clearAudio}>
        {clearStatus === "audio" ? "✓" : t("clear_audio_button")}
      </button>
      <button class="clear-btn" onclick={clearTranscriptions}>
        {clearStatus === "transcriptions" ? "✓" : t("clear_transcriptions_button")}
      </button>
    </div>
  </div>
</div>

<style>
  .recording-panel {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 1.5rem;
    padding: 2rem;
  }

  .mic-indicator {
    display: flex;
    align-items: center;
    gap: 1rem;
    padding: 1.5rem;
    border-radius: 50%;
    background: var(--bg-secondary);
    border: 2px solid var(--border);
    transition: all 0.3s;
  }

  .mic-indicator.active {
    border-color: #ff4444;
    box-shadow: 0 0 20px rgba(255, 68, 68, 0.3);
  }

  .mic-icon {
    font-size: 2rem;
  }

  .level-bars {
    display: flex;
    align-items: center;
    gap: 3px;
    height: 30px;
  }

  .bar {
    width: 4px;
    height: 8px;
    background: var(--border);
    border-radius: 2px;
    transition: height 0.15s;
  }

  .bar.active {
    height: 20px;
    background: var(--accent-green);
    animation: pulse 0.6s ease-in-out infinite alternate;
  }

  @keyframes pulse {
    from {
      height: 8px;
    }
    to {
      height: 28px;
    }
  }

  .record-btn {
    padding: 0.8rem 2rem;
    font-size: 1rem;
    font-weight: 600;
    border: none;
    border-radius: 8px;
    background: var(--accent);
    color: var(--bg-primary);
    cursor: pointer;
    transition: all 0.2s;
  }

  .record-btn:hover {
    filter: brightness(1.1);
  }

  .record-btn.recording {
    background: #ff4444;
    animation: recording-pulse 1.5s ease-in-out infinite;
  }

  .record-btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  @keyframes recording-pulse {
    0%,
    100% {
      box-shadow: 0 0 0 0 rgba(255, 68, 68, 0.4);
    }
    50% {
      box-shadow: 0 0 0 12px rgba(255, 68, 68, 0);
    }
  }

  .timer {
    font-size: 2.5rem;
    font-weight: 700;
    font-variant-numeric: tabular-nums;
    color: var(--text-primary);
    letter-spacing: 2px;
  }

  .transcription-preview {
    width: 100%;
    max-height: 150px;
    overflow-y: auto;
    padding: 1rem;
    background: var(--bg-secondary);
    border: 1px solid var(--border);
    border-radius: 8px;
    margin-top: 0.5rem;
  }

  .transcription-preview p {
    font-size: 0.9rem;
    line-height: 1.5;
    color: var(--text-secondary);
  }

  .error-msg {
    color: #ff4444;
    font-size: 0.85rem;
  }

  .file-info {
    width: 100%;
    display: flex;
    flex-direction: column;
    gap: 0.6rem;
    padding: 1rem;
    background: var(--bg-secondary);
    border: 1px solid var(--border);
    border-radius: 8px;
    margin-top: 0.5rem;
  }

  .info-row {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-size: 0.8rem;
    color: var(--text-secondary);
  }

  .info-separator {
    opacity: 0.5;
  }

  .clear-buttons {
    display: flex;
    gap: 0.5rem;
  }

  .clear-btn {
    flex: 1;
    padding: 0.4rem 0.6rem;
    font-size: 0.75rem;
    border: 1px solid var(--border);
    border-radius: 6px;
    background: transparent;
    color: var(--text-secondary);
    cursor: pointer;
    transition: all 0.2s;
  }

  .clear-btn:hover {
    border-color: #ff4444;
    color: #ff4444;
  }
</style>
