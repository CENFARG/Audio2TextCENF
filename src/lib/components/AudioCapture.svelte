<script lang="ts">
  import { APIClient } from '$lib/infrastructure/api-client';
  import { transcriptionState } from '$lib/state/transcription.svelte';
  import { createReconnectingWS } from '$lib/infrastructure/ws-reconnect';

  const api = new APIClient();
  let interval: ReturnType<typeof setInterval> | null = null;

  async function toggleRecording() {
    if (transcriptionState.recordingStatus === 'idle') {
      try {
        const { session_id } = await api.startRecording();
        transcriptionState.recordingStatus = 'recording';
        transcriptionState.elapsedSeconds = 0;

        interval = setInterval(() => {
          transcriptionState.elapsedSeconds += 1;
        }, 1000);

        const stream = api.connectStream();
        stream.onmessage = (event) => {
          const data = JSON.parse(event.data);
          if (data.type === 'partial') {
            transcriptionState.text += data.text;
          }
        };
      } catch {
        transcriptionState.recordingStatus = 'idle';
      }
    } else {
      interval && clearInterval(interval);
      transcriptionState.recordingStatus = 'processing';
      try {
        await api.stopRecording();
      } finally {
        transcriptionState.recordingStatus = 'idle';
      }
    }
  }
</script>

<button class="record-btn" class:recording={transcriptionState.recordingStatus === 'recording'} onclick={toggleRecording}>
  <span class="mic-icon">{transcriptionState.recordingStatus === 'recording' ? '⏹' : '🎤'}</span>
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