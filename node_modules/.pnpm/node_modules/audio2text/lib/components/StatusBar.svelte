<script lang="ts">
  let connected = $state(false);
  let provider = $state('mock');
</script>

<div class="status-bar">
  <span class="status-dot" class:online={connected}></span>
  <span class="provider">{provider}</span>
  <span class="status-text">{connected ? 'Conectado' : 'Sin conexión'}</span>
</div>

<style>
  .status-bar {
    display: flex;
    align-items: center;
    gap: var(--dt-spacing-sm);
    padding: var(--dt-spacing-sm) var(--dt-spacing-md);
    background: var(--dt-color-bg-secondary);
    border-top: 1px solid var(--dt-color-border-default);
    font-size: var(--dt-font-size-sm);
  }
  .status-dot {
    width: 8px; height: 8px;
    border-radius: 50%;
    background: var(--dt-color-text-muted);
  }
  .status-dot.online { background: var(--dt-color-status-success); }
  .provider { color: var(--dt-color-accent-default); font-weight: var(--dt-font-weight-medium); }
  .status-text { color: var(--dt-color-text-secondary); }
</style>