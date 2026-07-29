<script lang="ts">
  import { contextBlocks } from '$lib/state/transcription.svelte';

  function toggleBlock(id: string) {
    const idx = contextBlocks.selected.indexOf(id);
    if (idx >= 0) {
      contextBlocks.selected = contextBlocks.selected.filter(s => s !== id);
    } else {
      contextBlocks.selected = [...contextBlocks.selected, id];
    }
  }
</script>

<div class="selector">
  <h4>Bloques de contexto</h4>
  <label class="checkbox">
    <input type="checkbox" checked={contextBlocks.selected.includes('task_extractor')} onchange={() => toggleBlock('task_extractor')} />
    Extractor de Tareas
  </label>
  <label class="checkbox">
    <input type="checkbox" checked={contextBlocks.selected.includes('summary')} onchange={() => toggleBlock('summary')} />
    Generar Resumen
  </label>
  <label class="checkbox">
    <input type="checkbox" checked={contextBlocks.selected.includes('keyword_extractor')} onchange={() => toggleBlock('keyword_extractor')} />
    Palabras Clave
  </label>
</div>

<style>
  .selector {
    background: var(--dt-color-bg-secondary);
    padding: var(--dt-spacing-md);
    border-radius: var(--dt-radius-md);
    width: 200px;
  }
  h4 {
    margin: 0 0 var(--dt-spacing-sm);
    color: var(--dt-color-text-secondary);
    font-size: var(--dt-font-size-sm);
  }
  .checkbox {
    display: flex;
    align-items: center;
    gap: var(--dt-spacing-sm);
    padding: var(--dt-spacing-xs) 0;
    color: var(--dt-color-text-primary);
    font-size: var(--dt-font-size-sm);
    cursor: pointer;
  }
</style>