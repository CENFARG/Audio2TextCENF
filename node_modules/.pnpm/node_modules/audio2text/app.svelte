<script lang="ts">
  import { onMount } from 'svelte';
  import Navigation from './lib/components/Navigation.svelte';
  import TranscribeView from './lib/views/TranscribeView.svelte';
  import SettingsView from './lib/views/SettingsView.svelte';
  import HistoryView from './lib/views/HistoryView.svelte';
  import InfoView from './lib/views/InfoView.svelte';
  import UpdateView from './lib/views/UpdateView.svelte';
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
    {:else if currentView === 'settings'}
      <SettingsView />
    {:else if currentView === 'history'}
      <HistoryView />
    {:else if currentView === 'info'}
      <InfoView />
    {:else if currentView === 'update'}
      <UpdateView />
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