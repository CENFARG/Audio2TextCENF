<script lang="ts">
  import { onMount } from 'svelte';
  import Navigation from './lib/components/Navigation.svelte';
  import TranscribeView from './lib/views/TranscribeView.svelte';
  import './app.css';

  let currentView = $state('transcribe');

  onMount(async () => {
    // Bootstrap core-cenf-ts on mount
    try {
      const { bootstrap } = await import('./lib/infrastructure/bootstrap');
      await bootstrap();
    } catch (e) {
      console.warn('core-cenf-ts bootstrap skipped (not installed yet)');
    }
  });
</script>

<div class="app-container">
  <Navigation bind:currentView />
  <main class="content">
    {#if currentView === 'transcribe'}
      <TranscribeView />
    {:else if currentView === 'history'}
      <p>HistoryView — coming in Slice 4</p>
    {:else if currentView === 'settings'}
      <p>SettingsView — coming in Slice 3</p>
    {:else if currentView === 'info'}
      <p>InfoView — coming in Slice 4</p>
    {:else if currentView === 'update'}
      <p>UpdateView — coming in Slice 4</p>
    {/if}
  </main>
</div>

<style>
  .app-container {
    display: flex;
    height: 100vh;
    background: var(--dt-color-bg-primary);
  }
  .content {
    flex: 1;
    padding: var(--dt-spacing-lg);
    overflow-y: auto;
  }
</style>