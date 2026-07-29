<script lang="ts">
  export let currentView: string;

  const tabs = [
    { id: 'transcribe', label: 'Transcribir', icon: '🎤' },
    { id: 'history', label: 'Historial', icon: '📋' },
    { id: 'settings', label: 'Ajustes', icon: '⚙️' },
    { id: 'info', label: 'Info', icon: 'ℹ️' },
    { id: 'update', label: 'Actualizar', icon: '📦' },
  ];
</script>

<nav class="sidebar">
  <div class="sidebar-header">
    <h2>Audio2Text</h2>
  </div>
  {#each tabs as tab}
    <button
      class="nav-item"
      class:active={currentView === tab.id}
      onclick={() => currentView = tab.id}
    >
      <span class="nav-icon">{tab.icon}</span>
      <span>{tab.label}</span>
    </button>
  {/each}
</nav>

<style>
  .sidebar {
    width: 220px;
    background: var(--dt-color-bg-secondary);
    padding: var(--dt-spacing-md);
    border-right: 1px solid var(--dt-color-border-default);
    display: flex;
    flex-direction: column;
    gap: var(--dt-spacing-sm);
  }
  .sidebar-header {
    padding: var(--dt-spacing-md);
    border-bottom: 1px solid var(--dt-color-border-default);
    margin-bottom: var(--dt-spacing-sm);
  }
  .sidebar-header h2 {
    margin: 0;
    font-size: var(--dt-font-size-lg);
    color: var(--dt-color-accent-default);
  }
  .nav-item {
    display: flex;
    align-items: center;
    gap: var(--dt-spacing-sm);
    padding: var(--dt-spacing-md);
    background: transparent;
    border: none;
    border-radius: var(--dt-radius-md);
    color: var(--dt-color-text-secondary);
    cursor: pointer;
    font-size: var(--dt-font-size-base);
    font-family: var(--dt-font-family);
    text-align: left;
    width: 100%;
    transition: background var(--dt-transition-fast);
  }
  .nav-item:hover {
    background: var(--dt-color-bg-hover);
  }
  .nav-item.active {
    background: var(--dt-color-accent-muted);
    color: var(--dt-color-accent-default);
    border-left: 3px solid var(--dt-color-accent-default);
  }
  .nav-icon {
    font-size: var(--dt-font-size-lg);
  }
</style>