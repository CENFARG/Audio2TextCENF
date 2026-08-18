<script lang="ts">
  import RecordingPanel from "./components/RecordingPanel.svelte";
  import History from "./components/History.svelte";
  import Settings from "./components/Settings.svelte";
  import Info from "./components/Info.svelte";
  import LanguageSwitch from "./components/LanguageSwitch.svelte";
  import StatusBar from "./components/StatusBar.svelte";
  import { t } from "./lib/i18n.svelte";

  let activeTab = $state<"recording" | "history" | "settings" | "info">("recording");
</script>

<div class="app">
  <header class="app-header">
    <h1>Audio2Text</h1>
    <LanguageSwitch />
  </header>

  <nav class="tabs">
    <button
      class="tab"
      class:active={activeTab === "recording"}
      onclick={() => (activeTab = "recording")}
    >
      {t("tab_main")}
    </button>
    <button
      class="tab"
      class:active={activeTab === "history"}
      onclick={() => (activeTab = "history")}
    >
      {t("tab_history")}
    </button>
    <button
      class="tab"
      class:active={activeTab === "settings"}
      onclick={() => (activeTab = "settings")}
    >
      {t("tab_settings")}
    </button>
    <button
      class="tab"
      class:active={activeTab === "info"}
      onclick={() => (activeTab = "info")}
    >
      {t("tab_info")}
    </button>
  </nav>

  <main class="content">
    {#if activeTab === "recording"}
      <RecordingPanel />
    {:else if activeTab === "history"}
      <History />
    {:else if activeTab === "settings"}
      <Settings />
    {:else}
      <Info />
    {/if}
  </main>

  <StatusBar />
</div>

<style>
  .app {
    display: flex;
    flex-direction: column;
    height: 100vh;
    background: var(--bg-primary);
  }

  .app-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.75rem 1.25rem;
    border-bottom: 1px solid var(--border);
  }

  h1 {
    font-size: 1.1rem;
    color: var(--accent);
    font-weight: 700;
  }

  .tabs {
    display: flex;
    border-bottom: 1px solid var(--border);
  }

  .tab {
    flex: 1;
    padding: 0.6rem;
    font-size: 0.85rem;
    font-weight: 500;
    border: none;
    background: transparent;
    color: var(--text-secondary);
    cursor: pointer;
    transition: color 0.2s, border-color 0.2s;
    border-bottom: 2px solid transparent;
  }

  .tab:hover {
    color: var(--text-primary);
  }

  .tab.active {
    color: var(--accent);
    border-bottom-color: var(--accent);
  }

  .content {
    flex: 1;
    overflow-y: auto;
  }
</style>
