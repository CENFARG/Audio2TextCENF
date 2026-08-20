<script lang="ts">
  import { defaultTabs, type TabConfig } from './navigation/tabs';

  let { currentView = $bindable() } = $props<{ currentView: string }>();
  let activeSubTab = $state('');

  function isSettings(id: string): boolean {
    return id.startsWith('settings');
  }

  function handleTabClick(tab: TabConfig) {
    if (tab.children?.length) {
      // Toggle settings submenu: set active view to 'settings' and expand
      currentView = 'settings';
      activeSubTab = activeSubTab ? '' : tab.children[0].id;
    } else {
      currentView = tab.id;
      activeSubTab = '';
    }
  }
</script>

<nav class="sidebar">
  <div class="sidebar-header">
    <h2>Audio2Text</h2>
    <span class="version-badge">v0.16.0</span>
  </div>

  {#each defaultTabs.filter(t => t.enabled) as tab}
    <button
      class="nav-item"
      class:active={currentView === tab.id || (isSettings(currentView) && tab.id === 'settings')}
      onclick={() => handleTabClick(tab)}
    >
      <span class="nav-icon">{tab.icon}</span>
      <span>{tab.label}</span>
    </button>

    {#if tab.children && (isSettings(currentView) || activeSubTab)}
      <div class="sub-tabs">
        {#each tab.children.filter(c => c.enabled) as sub}
          <button
            class="sub-tab"
            class:active={activeSubTab === sub.id}
            onclick={() => activeSubTab = sub.id}
          >
            <span class="sub-icon">{sub.icon}</span>
            <span>{sub.label}</span>
          </button>
        {/each}
      </div>
    {/if}
  {/each}
</nav>

<style>
  .sidebar {
    width: 240px;
    background: var(--dt-color-bg-secondary);
    padding: var(--dt-spacing-md);
    border-right: 1px solid var(--dt-color-border-default);
    display: flex;
    flex-direction: column;
    gap: var(--dt-spacing-xs);
    overflow-y: auto;
    user-select: none;
  }
  .sidebar-header {
    padding: var(--dt-spacing-md);
    border-bottom: 1px solid var(--dt-color-border-default);
    margin-bottom: var(--dt-spacing-sm);
    display: flex;
    align-items: baseline;
    gap: var(--dt-spacing-sm);
  }
  .sidebar-header h2 {
    margin: 0;
    font-size: var(--dt-font-size-lg);
    color: var(--dt-color-accent-default);
  }
  .version-badge {
    font-size: var(--dt-font-size-xs);
    color: var(--dt-color-text-muted);
  }
  .nav-item {
    display: flex;
    align-items: center;
    gap: var(--dt-spacing-sm);
    padding: var(--dt-spacing-sm) var(--dt-spacing-md);
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
  .nav-item:hover { background: var(--dt-color-bg-hover); }
  .nav-item.active {
    background: var(--dt-color-accent-muted);
    color: var(--dt-color-accent-default);
    border-left: 3px solid var(--dt-color-accent-default);
    font-weight: var(--dt-font-weight-semibold);
  }
  .nav-icon { font-size: var(--dt-font-size-lg); width: 24px; text-align: center; }

  .sub-tabs {
    margin-left: var(--dt-spacing-xl);
    border-left: 1px solid var(--dt-color-border-default);
    padding-left: 0;
  }
  .sub-tab {
    display: flex;
    align-items: center;
    gap: var(--dt-spacing-sm);
    padding: var(--dt-spacing-xs) var(--dt-spacing-md);
    background: transparent;
    border: none;
    border-radius: var(--dt-radius-sm);
    color: var(--dt-color-text-muted);
    cursor: pointer;
    font-size: var(--dt-font-size-sm);
    font-family: var(--dt-font-family);
    width: 100%;
    text-align: left;
  }
  .sub-tab:hover { color: var(--dt-color-text-secondary); }
  .sub-tab.active {
    color: var(--dt-color-accent-default);
    font-weight: var(--dt-font-weight-semibold);
  }
  .sub-icon { font-size: var(--dt-font-size-sm); width: 18px; }
</style>