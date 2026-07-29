<script lang="ts">
  import AudioCapture from '$lib/components/AudioCapture.svelte';
  import RecordingOverlay from '$lib/components/RecordingOverlay.svelte';
  import TranscriptionPanel from '$lib/components/TranscriptionPanel.svelte';
  import StatusBar from '$lib/components/StatusBar.svelte';
  import ContextBlocksSelector from '$lib/components/ContextBlocksSelector.svelte';
</script>

<div class="transcribe-view">
  <div class="main-area">
    <div class="controls">
      <AudioCapture />
    </div>
    <TranscriptionPanel />
    <StatusBar />
  </div>
  <aside class="sidebar">
    <ContextBlocksSelector />
  </aside>
</div>
<RecordingOverlay />

<style>
  .transcribe-view {
    display: flex;
    height: 100%;
    gap: var(--dt-spacing-md);
  }
  .main-area {
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: var(--dt-spacing-md);
  }
  .controls {
    display: flex;
    justify-content: center;
  }
  aside.sidebar {
    width: 220px;
    flex-shrink: 0;
  }
</style>