<script lang="ts">
  let appVersion = '0.16.0';
  let apiVersion = $state('');
  let pythonVersion = $state('');
  let platformInfo = $state('');

  $effect(() => {
    pythonVersion = 'Python 3.12';
    platformInfo = navigator.platform || 'Windows';
  });
</script>

<div class="info-view">
  <h2>Información</h2>

  <div class="info-grid">
    <div class="info-card">
      <span class="label">Audio2Text</span>
      <span class="value accent">v{appVersion}</span>
    </div>
    <div class="info-card">
      <span class="label">API Backend</span>
      <span class="value">{apiVersion || '—'}</span>
    </div>
    <div class="info-card">
      <span class="label">Python</span>
      <span class="value">{pythonVersion}</span>
    </div>
    <div class="info-card">
      <span class="label">Plataforma</span>
      <span class="value">{platformInfo}</span>
    </div>
  </div>

  <div class="credits">
    <h3>Créditos</h3>
    <p>Desarrollado por CENF Development Team</p>
    <p>Tecnologías: Tauri v2, Svelte 5, FastAPI, core-cenf-py/ts</p>
    <p>Licencia: Apache 2.0</p>
  </div>

  <div class="links">
    <a href="https://github.com/CENFARG/Audio2TextCENF" target="_blank">GitHub</a>
    <a href="https://cenf.tech" target="_blank">cenf.tech</a>
  </div>
</div>

<style>
  .info-view {
    padding: var(--dt-spacing-xl);
    max-width: 500px;
    display: flex;
    flex-direction: column;
    gap: var(--dt-spacing-xl);
  }
  h2 { color: var(--dt-color-accent-default); margin: 0; }
  h3 { color: var(--dt-color-text-primary); margin: 0 0 var(--dt-spacing-sm); }

  .info-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: var(--dt-spacing-md);
  }
  .info-card {
    background: var(--dt-color-bg-secondary);
    padding: var(--dt-spacing-md);
    border-radius: var(--dt-radius-md);
    display: flex;
    flex-direction: column;
    gap: var(--dt-spacing-xs);
  }
  .label { font-size: var(--dt-font-size-xs); color: var(--dt-color-text-muted); text-transform: uppercase; }
  .value { font-size: var(--dt-font-size-lg); color: var(--dt-color-text-primary); font-weight: var(--dt-font-weight-semibold); }
  .value.accent { color: var(--dt-color-accent-default); }

  .credits p { font-size: var(--dt-font-size-sm); color: var(--dt-color-text-secondary); margin: var(--dt-spacing-xs) 0; }
  .links { display: flex; gap: var(--dt-spacing-md); }
  .links a { color: var(--dt-color-accent-default); text-decoration: none; font-size: var(--dt-font-size-sm); }
</style>