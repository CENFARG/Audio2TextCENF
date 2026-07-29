<script lang="ts">
  import { transcriptionState } from '$lib/state/transcription.svelte';
</script>

<div class="panel" class:empty={!transcriptionState.text}>
  {#if transcriptionState.text}
    <pre class="text">{transcriptionState.text}</pre>
  {:else}
    <p class="placeholder">La transcripción aparecerá aquí...</p>
  {/if}
</div>

<style>
  .panel {
    flex: 1;
    background: var(--dt-color-bg-secondary);
    border-radius: var(--dt-radius-md);
    padding: var(--dt-spacing-md);
    overflow-y: auto;
    min-height: 200px;
  }
  .text {
    margin: 0;
    font-family: var(--dt-font-family-mono);
    font-size: var(--dt-font-size-base);
    color: var(--dt-color-text-primary);
    white-space: pre-wrap;
    word-wrap: break-word;
  }
  .placeholder {
    color: var(--dt-color-text-muted);
    text-align: center;
    padding: var(--dt-spacing-xl);
  }
</style>