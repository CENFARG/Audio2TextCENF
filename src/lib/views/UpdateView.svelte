<script lang="ts">
  import { APIClient } from '$lib/infrastructure/api-client';

  const api = new APIClient();
  let checking = $state(false);
  let updateAvailable = $state(false);
  let latestVersion = $state('');
  let status = $state('');

  async function checkUpdate() {
    checking = true;
    try {
      const result = await api.checkUpdate();
      updateAvailable = result.available;
      latestVersion = result.version || '';
      status = updateAvailable ? `v${latestVersion} disponible` : 'Estás en la última versión';
    } catch {
      status = 'Error al verificar actualizaciones';
    } finally {
      checking = false;
    }
  }
</script>

<div class="update-view">
  <h2>Actualizaciones</h2>

  <div class="update-card">
    <p class="current-version">Versión actual: <span class="accent">v0.16.0</span></p>

    <button class="check-btn" onclick={checkUpdate} disabled={checking}>
      {checking ? 'Verificando...' : 'Buscar Actualizaciones'}
    </button>

    {#if status}
      <p class="status" class:success={updateAvailable}>{status}</p>
    {/if}

    {#if updateAvailable}
      <button class="download-btn">Descargar v{latestVersion}</button>
    {/if}
  </div>
</div>

<style>
  .update-view {
    padding: var(--dt-spacing-xl);
    max-width: 400px;
  }
  h2 { color: var(--dt-color-accent-default); margin: 0 0 var(--dt-spacing-lg); }

  .update-card {
    background: var(--dt-color-bg-secondary);
    padding: var(--dt-spacing-xl);
    border-radius: var(--dt-radius-lg);
    display: flex;
    flex-direction: column;
    gap: var(--dt-spacing-md);
  }
  .current-version { font-size: var(--dt-font-size-base); color: var(--dt-color-text-secondary); }
  .accent { color: var(--dt-color-accent-default); font-weight: var(--dt-font-weight-semibold); }

  .check-btn {
    padding: var(--dt-spacing-md); background: var(--dt-color-accent-default);
    color: var(--dt-color-bg-primary); border: none; border-radius: var(--dt-radius-md);
    cursor: pointer; font-family: var(--dt-font-family); font-size: var(--dt-font-size-base);
    font-weight: var(--dt-font-weight-semibold);
  }
  .check-btn:disabled { opacity: 0.5; cursor: not-allowed; }

  .status { font-size: var(--dt-font-size-sm); color: var(--dt-color-text-muted); }
  .status.success { color: var(--dt-color-status-success); }

  .download-btn {
    padding: var(--dt-spacing-md); background: var(--dt-color-status-success);
    color: white; border: none; border-radius: var(--dt-radius-md);
    cursor: pointer; font-family: var(--dt-font-family); font-weight: var(--dt-font-weight-semibold);
  }
</style>