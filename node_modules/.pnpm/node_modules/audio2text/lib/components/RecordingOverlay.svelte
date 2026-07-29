<script lang="ts">
  import { transcriptionState } from '$lib/state/transcription.svelte';

  let minutes = $derived(Math.floor(transcriptionState.elapsedSeconds / 60));
  let seconds = $derived(transcriptionState.elapsedSeconds % 60);
  let timerDisplay = $derived(`${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`);
</script>

{#if transcriptionState.recordingStatus !== 'idle'}
  <div class="overlay">
    <div class="overlay-content">
      <div class="led" class:recording={transcriptionState.recordingStatus === 'recording'}></div>
      <span class="timer">{timerDisplay}</span>
      <div class="actions">
        <button class="btn cancel" onclick={() => transcriptionState.recordingStatus = 'idle'}>Cancelar</button>
        <button class="btn stop" onclick={() => transcriptionState.recordingStatus = 'idle'}>Detener</button>
      </div>
    </div>
  </div>
{/if}

<style>
  .overlay {
    position: fixed;
    inset: 0;
    background: var(--dt-color-bg-overlay);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: var(--dt-z-modal);
  }
  .overlay-content {
    background: var(--dt-color-bg-secondary);
    padding: var(--dt-spacing-xl);
    border-radius: var(--dt-radius-lg);
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: var(--dt-spacing-lg);
  }
  .led {
    width: 24px;
    height: 24px;
    border-radius: 50%;
    background: var(--dt-color-status-danger);
  }
  .led.recording {
    animation: pulse-led 1s infinite;
  }
  @keyframes pulse-led {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.3; }
  }
  .timer {
    font-size: var(--dt-font-size-xxl);
    font-weight: var(--dt-font-weight-bold);
    color: var(--dt-color-text-primary);
    font-family: var(--dt-font-family-mono);
  }
  .actions {
    display: flex;
    gap: var(--dt-spacing-md);
  }
  .btn {
    padding: var(--dt-spacing-sm) var(--dt-spacing-lg);
    border-radius: var(--dt-radius-md);
    border: none;
    cursor: pointer;
    font-family: var(--dt-font-family);
    font-size: var(--dt-font-size-base);
  }
  .cancel { background: var(--dt-color-bg-tertiary); color: var(--dt-color-text-secondary); }
  .stop { background: var(--dt-color-accent-default); color: var(--dt-color-bg-primary); }
</style>