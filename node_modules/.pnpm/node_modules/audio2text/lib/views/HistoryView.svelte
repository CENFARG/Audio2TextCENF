<script lang="ts">
  import { APIClient } from '$lib/infrastructure/api-client';

  const api = new APIClient();
  let items = $state<Array<Record<string, unknown>>>([]);
  let search = $state('');
  let selected = $state<Record<string, unknown> | null>(null);
  let emojiOpen = $state(false);

  const EMOJIS = ['⭐','📝','💡','🎯','📋','🔑','💬','📌','🏷️','📎','📂','🗂️','🔖','✏️','📄'];

  async function load() {
    try { items = await api.getHistory(); } catch { /* silent */ }
  }

  function selectItem(item: Record<string, unknown>) { selected = item; emojiOpen = false; }
  async function assignEmoji(emoji: string) {
    if (!selected) return;
    await api.updateTranscription(String(selected.id), { emoji });
    selected = { ...selected, emoji };
    emojiOpen = false;
    load();
  }
  async function deleteItem(id: string) {
    await api.deleteTranscription(id);
    selected = null;
    load();
  }

  $effect(() => { load(); });

  let filtered = $derived(items.filter(i =>
    String(i.title || '').toLowerCase().includes(search.toLowerCase()) ||
    String(i.filename || '').toLowerCase().includes(search.toLowerCase())
  ));
</script>

<div class="history-view">
  <div class="list-panel">
    <div class="search-bar">
      <input type="text" bind:value={search} placeholder="Buscar transcripciones..." />
    </div>
    <div class="list">
      {#each filtered as item}
        <button class="item" class:selected={selected?.id === item.id} onclick={() => selectItem(item)}>
          <span class="emoji">{item.emoji || '📄'}</span>
          <span class="title">{item.title || item.filename}</span>
          <span class="date">{String(item.created_at || '').slice(0, 10)}</span>
        </button>
      {/each}
    </div>
  </div>

  <div class="detail-panel">
    {#if selected}
      <div class="detail-header">
        <button class="emoji-btn" onclick={() => emojiOpen = !emojiOpen}>
          {selected.emoji || '📄'}
        </button>
        <h3>{selected.title || selected.filename}</h3>
        <button class="delete-btn" onclick={() => deleteItem(String(selected.id))}>🗑️</button>
      </div>
      {#if emojiOpen}
        <div class="emoji-picker">
          {#each EMOJIS as emoji}
            <button class="emoji-option" onclick={() => assignEmoji(emoji)}>{emoji}</button>
          {/each}
        </div>
      {/if}
      <div class="detail-body">
        {#if selected.text}
          <pre class="transcript-text">{selected.text}</pre>
        {/if}
        <div class="meta">
          <span>Proveedor: {selected.provider || '—'}</span>
          <span>Idioma: {selected.language || '—'}</span>
          <span>Duración: {selected.duration_s ? String(selected.duration_s) + 's' : '—'}</span>
        </div>
      </div>
    {:else}
      <p class="empty-message">Seleccioná una transcripción para ver detalles</p>
    {/if}
  </div>
</div>

<style>
  .history-view { display: flex; height: 100%; }
  .list-panel { width: 320px; display: flex; flex-direction: column; border-right: 1px solid var(--dt-color-border-default); }
  .search-bar { padding: var(--dt-spacing-md); }
  .search-bar input {
    width: 100%; padding: var(--dt-spacing-sm); background: var(--dt-color-bg-tertiary);
    border: 1px solid var(--dt-color-border-default); border-radius: var(--dt-radius-sm);
    color: var(--dt-color-text-primary); font-family: var(--dt-font-family);
  }
  .list { flex: 1; overflow-y: auto; }
  .item {
    display: flex; align-items: center; gap: var(--dt-spacing-sm);
    padding: var(--dt-spacing-sm) var(--dt-spacing-md); width: 100%;
    background: transparent; border: none; border-bottom: 1px solid var(--dt-color-border-default);
    color: var(--dt-color-text-secondary); cursor: pointer; font-family: var(--dt-font-family);
    text-align: left;
  }
  .item:hover { background: var(--dt-color-bg-hover); }
  .item.selected { background: var(--dt-color-accent-muted); color: var(--dt-color-accent-default); }
  .emoji { font-size: var(--dt-font-size-lg); }
  .title { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .date { font-size: var(--dt-font-size-xs); color: var(--dt-color-text-muted); }

  .detail-panel { flex: 1; padding: var(--dt-spacing-lg); display: flex; flex-direction: column; }
  .detail-header { display: flex; align-items: center; gap: var(--dt-spacing-md); margin-bottom: var(--dt-spacing-md); }
  .detail-header h3 { margin: 0; flex: 1; color: var(--dt-color-text-primary); }
  .emoji-btn { font-size: 28px; background: none; border: none; cursor: pointer; }
  .delete-btn { background: var(--dt-color-status-danger-bg); border: none; border-radius: var(--dt-radius-sm); padding: var(--dt-spacing-sm); cursor: pointer; }

  .emoji-picker { display: flex; flex-wrap: wrap; gap: var(--dt-spacing-xs); padding: var(--dt-spacing-sm); background: var(--dt-color-bg-secondary); border-radius: var(--dt-radius-md); margin-bottom: var(--dt-spacing-md); }
  .emoji-option { font-size: 20px; background: none; border: none; cursor: pointer; padding: var(--dt-spacing-xs); border-radius: var(--dt-radius-sm); }
  .emoji-option:hover { background: var(--dt-color-bg-hover); }

  .detail-body { flex: 1; }
  .transcript-text { white-space: pre-wrap; font-family: var(--dt-font-family-mono); font-size: var(--dt-font-size-sm); color: var(--dt-color-text-primary); background: var(--dt-color-bg-secondary); padding: var(--dt-spacing-md); border-radius: var(--dt-radius-md); max-height: 300px; overflow-y: auto; }
  .meta { display: flex; gap: var(--dt-spacing-lg); padding-top: var(--dt-spacing-md); font-size: var(--dt-font-size-sm); color: var(--dt-color-text-muted); }
  .empty-message { text-align: center; color: var(--dt-color-text-muted); padding: var(--dt-spacing-xxl); }
</style>