<script lang="ts">
  import { getRecordingState, startRecording, stopRecording } from '$lib/stores/recording.svelte';

  // Single Owner: recording state + capture live in recording.svelte.ts + FastAPI.
  // This button is a view: toggles the same path as F9/tray.

  let rec = $derived(getRecordingState());

  async function toggleRecording() {
    if (rec.isRecording) {
      await stopRecording();
    } else {
      await startRecording();
    }
  }
</script>

<button
  class="record-btn"
  class:recording={rec.isRecording}
  onclick={toggleRecording}
  title={rec.isRecording ? 'Detener grabación' : 'Comenzar grabación'}
>
  <span class="mic-icon">{rec.isRecording ? '⏹' : '🎤'}</span>
</button>

<style>
  .record-btn {
    width: 64px;
    height: 64px;
    border-radius: 50%;
    border: 2px solid var(--dt-color-border-default);
    background: var(--dt-color-bg-secondary);
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all var(--dt-transition-fast);
  }
  .record-btn:hover { background: var(--dt-color-bg-hover); }
  .record-btn.recording {
    background: var(--dt-color-status-danger);
    border-color: var(--dt-color-status-danger);
    animation: pulse 1.5s infinite;
  }
  .mic-icon { font-size: 24px; }
  @keyframes pulse {
    0%, 100% { box-shadow: 0 0 0 0 var(--dt-color-status-danger-bg); }
    50% { box-shadow: 0 0 0 12px transparent; }
  }
</style>