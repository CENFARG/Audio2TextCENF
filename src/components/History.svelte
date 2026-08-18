<script lang="ts">
  import { getHistory } from "../lib/commands";
  import { t } from "../lib/i18n.svelte";

  interface HistoryItem {
    filename: string;
    date: string;
    preview: string;
  }

  let items = $state<HistoryItem[]>([]);
  let searchQuery = $state("");
  let copiedIndex = $state<number | null>(null);

  let filteredItems = $derived(
    searchQuery
      ? items.filter(
          (item) =>
            item.filename.toLowerCase().includes(searchQuery.toLowerCase()) ||
            item.preview.toLowerCase().includes(searchQuery.toLowerCase()),
        )
      : items,
  );

  async function loadHistory(): Promise<void> {
    const response = await getHistory();
    if (response.status === "ok" && Array.isArray(response.data)) {
      items = response.data as HistoryItem[];
    }
  }

  async function copyToClipboard(text: string, index: number): Promise<void> {
    try {
      await navigator.clipboard.writeText(text);
      copiedIndex = index;
      setTimeout(() => {
        copiedIndex = null;
      }, 1500);
    } catch {
      // clipboard not available in some Tauri contexts
    }
  }

  function formatDate(dateStr: string): string {
    try {
      return new Date(dateStr).toLocaleDateString();
    } catch {
      return dateStr;
    }
  }

  $effect(() => {
    loadHistory();
  });
</script>

<div class="history">
  <div class="history-header">
    <h2>{t("history_title")}</h2>
    <button class="refresh-btn" onclick={loadHistory}>
      {t("refresh_button")}
    </button>
  </div>

  <input
    type="text"
    class="search-input"
    placeholder="Buscar..."
    bind:value={searchQuery}
  />

  {#if filteredItems.length === 0}
    <p class="empty">{t("history_no_files")}</p>
  {:else}
    <div class="history-list">
      {#each filteredItems as item, i}
        <button
          class="history-item"
          class:copied={copiedIndex === i}
          onclick={() => copyToClipboard(item.preview, i)}
        >
          <div class="item-header">
            <span class="filename">{item.filename}</span>
            <span class="date">{formatDate(item.date)}</span>
          </div>
          <p class="preview">{item.preview}</p>
          {#if copiedIndex === i}
            <span class="copied-badge">Copiado</span>
          {/if}
        </button>
      {/each}
    </div>
  {/if}
</div>

<style>
  .history {
    display: flex;
    flex-direction: column;
    gap: 1rem;
    padding: 1.5rem;
    height: 100%;
  }

  .history-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  h2 {
    font-size: 1.2rem;
    color: var(--accent);
  }

  .refresh-btn {
    padding: 0.4rem 0.8rem;
    font-size: 0.8rem;
    border: 1px solid var(--border);
    border-radius: 6px;
    background: var(--bg-secondary);
    color: var(--text-primary);
    cursor: pointer;
  }

  .refresh-btn:hover {
    border-color: var(--accent);
  }

  .search-input {
    padding: 0.6rem 1rem;
    border: 1px solid var(--border);
    border-radius: 6px;
    background: var(--bg-secondary);
    color: var(--text-primary);
    font-size: 0.9rem;
    outline: none;
  }

  .search-input:focus {
    border-color: var(--accent);
  }

  .empty {
    text-align: center;
    color: var(--text-secondary);
    padding: 2rem;
    font-style: italic;
  }

  .history-list {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    overflow-y: auto;
    flex: 1;
  }

  .history-item {
    display: block;
    width: 100%;
    text-align: left;
    padding: 0.8rem 1rem;
    background: var(--bg-secondary);
    border: 1px solid var(--border);
    border-radius: 8px;
    cursor: pointer;
    transition: border-color 0.2s;
    position: relative;
    font: inherit;
    color: inherit;
  }

  .history-item:hover {
    border-color: var(--accent);
  }

  .history-item.copied {
    border-color: var(--accent-green);
  }

  .item-header {
    display: flex;
    justify-content: space-between;
    margin-bottom: 0.3rem;
  }

  .filename {
    font-weight: 600;
    font-size: 0.85rem;
    color: var(--text-primary);
  }

  .date {
    font-size: 0.75rem;
    color: var(--text-secondary);
  }

  .preview {
    font-size: 0.8rem;
    color: var(--text-secondary);
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .copied-badge {
    position: absolute;
    top: 0.5rem;
    right: 0.5rem;
    font-size: 0.7rem;
    padding: 0.15rem 0.4rem;
    background: var(--accent-green);
    color: var(--bg-primary);
    border-radius: 4px;
    font-weight: 600;
  }
</style>
