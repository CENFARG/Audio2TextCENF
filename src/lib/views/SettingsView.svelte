<script lang="ts">
  import { onMount } from 'svelte';
  import { APIClient } from '$lib/infrastructure/api-client';

  const api = new APIClient();
  let expanded = $state<string | null>(null);
  let saving = $state(false);
  let status = $state<'idle' | 'saving' | 'saved' | 'error'>('idle');
  let statusMessage = $state('');
  let isLoaded = $state(false);
  let debounceTimeout: ReturnType<typeof setTimeout> | undefined;
  let settings: Record<string, unknown> = $state({
    provider: 'mock', groq_api_key: '', nvidia_api_key: '',
    groq_model: 'whisper-large-v3', fw_model: 'base', fw_device: 'auto',
    audio_path: './audio', transcriptions_path: './transcriptions',
    save_audio: true, max_files: 100, auto_cleanup: false,
    record_mode: 'toggle', max_recording_time: '10min',
    auto_paste: true, show_overlay: true, start_with_windows: false,
    post_process: true, ai_model: 'llama-3.1-70b', ai_profile: 'medium',
    task_extractor: true, summary: true, keyword_extractor: true,
    hotkey: 'Ctrl+Shift+R', language: 'es_ES',
  });

  function toggle(id: string) { expanded = expanded === id ? null : id; }

  onMount(async () => {
    try {
      const loaded = await api.getSettings() as Record<string, unknown>;
      // api.getSettings now returns data.config ?? data, so loaded may be the config dict directly
      // Normalize: if loaded has 'config' key, use it, otherwise loaded itself is config
      const cfg: Record<string, unknown> = (loaded as any)?.providers ? loaded as Record<string, unknown> : (loaded as Record<string, unknown>) ?? {};
      const providers = (cfg.providers ?? (cfg as any)?.config?.providers) as Record<string, unknown> | undefined;
      const primary = (providers?.primary ?? (cfg as any).primary ?? (cfg as any)?.config?.providers?.primary) as string | undefined;
      if (primary) {
        settings.provider = primary;
      } else if ((cfg as any)?.providers?.primary) {
        settings.provider = (cfg as any).providers.primary;
      }
      // Handle secrets masking: if cfg contains masked values, keep input empty and show placeholder
      // No need to set real value; leave groq_api_key empty so UI shows placeholder ••••
      // Also handle groq model mapping if present
      const groqModel = (cfg.providers as Record<string, unknown> | undefined)?.groq ?? (cfg as Record<string, unknown>).groq;
      if (providers && (providers as Record<string, unknown>).groq && typeof (providers as Record<string, unknown>).groq === 'object') {
        const g = (providers as Record<string, unknown>).groq as Record<string, unknown>;
        if (g.model) settings.groq_model = g.model as string;
      } else if ((cfg as any)?.providers?.groq?.model) {
        settings.groq_model = (cfg as any).providers.groq.model;
      }
    } catch (e) {
      console.warn("[SettingsView] load failed", e);
      status = 'error';
      statusMessage = `Error cargando ajustes`;
    } finally {
      isLoaded = true;
    }
  });

  async function save() {
    if (!isLoaded) return;
    saving = true;
    status = 'saving';
    statusMessage = '';
    try {
      const secrets: Record<string, string> = {};
      const groqKey = String(settings.groq_api_key ?? '').trim();
      const nvidiaKey = String(settings.nvidia_api_key ?? '').trim();
      if (groqKey && groqKey !== '***' && groqKey !== '••••' && groqKey.length > 0) {
        secrets.groq_api_key = groqKey;
      }
      if (nvidiaKey && nvidiaKey !== '***' && nvidiaKey !== '••••' && nvidiaKey.length > 0) {
        secrets.nvidia_api_key = nvidiaKey;
      }
      const providers: Record<string, unknown> = { primary: settings.provider as string };
      // Map groq_model -> providers.groq.model
      if (settings.groq_model) {
        providers.groq = { model: settings.groq_model as string };
      }
      if (settings.fw_model || settings.fw_device) {
        const fw: Record<string, unknown> = {};
        if (settings.fw_model) fw.model = settings.fw_model;
        if (settings.fw_device) fw.device = settings.fw_device;
        // merge with existing groq provider? keep separate
        // Use faster_whisper key as in factory
        (providers as Record<string, unknown>).faster_whisper = fw;
      }
      const config: Record<string, unknown> = { providers };
      if (Object.keys(secrets).length > 0) {
        (config as Record<string, unknown>).secrets = secrets;
      }
      await api.saveSettings({ config });
      status = 'saved';
      statusMessage = 'Guardado ✓';
      setTimeout(() => { if (status === 'saved') { status = 'idle'; statusMessage = ''; } }, 2000);
    } catch (e) {
      status = 'error';
      statusMessage = `Error: ${e}`;
      console.warn("[SettingsView] save failed", e);
    } finally {
      saving = false;
    }
  }

  // Debounce for text inputs (provider/api keys)
  $effect(() => {
    void settings.provider;
    void settings.groq_api_key;
    void settings.nvidia_api_key;
    void settings.groq_model;
    if (!isLoaded) return;
    clearTimeout(debounceTimeout);
    debounceTimeout = setTimeout(() => { save(); }, 400);
  });

  function handleProviderChange() {
    // immediate save on provider select
    clearTimeout(debounceTimeout);
    save();
  }
</script>

<div class="settings-view">
  <div class="settings-header">
    <h2>Ajustes</h2>
    {#if saving || status === 'saving'}<span class="saving-badge">Guardando...</span>
    {:else if status === 'saved'}<span class="saving-badge">Guardado ✓</span>
    {:else if status === 'error'}<span class="error-badge">{statusMessage}</span>
    {/if}
    {#if settings.provider === 'mock'}<span class="mock-badge">Mock siempre disponible — no necesita API key</span>{/if}
  </div>

  <section class="panel-section">
    <button class="panel-header" onclick={() => toggle('provider')}>
      <span>🔌 Proveedor</span>
      <span class="chevron">{expanded === 'provider' ? '▾' : '▸'}</span>
    </button>
    {#if expanded === 'provider'}
    <div class="panel-body">
      <label>Proveedor principal <select bind:value={settings.provider} onchange={handleProviderChange}>
        <option value="groq">Groq Cloud</option>
        <option value="faster_whisper">Faster Whisper (local)</option>
        <option value="nvidia">NVIDIA Riva</option>
        <option value="mock">Mock (testing)</option>
      </select></label>
      {#if settings.provider === 'mock'}
        <div class="mock-info">Mock siempre disponible — no necesita API key</div>
      {:else if settings.provider === 'groq' && !String(settings.groq_api_key ?? '').trim()}
        <div class="warning-info">Groq no configurado — pega gsk_... para activar</div>
      {/if}
      <label>Groq API Key <input type="password" bind:value={settings.groq_api_key} placeholder="••••" onchange={save} /></label>
      <label>Groq Model <input bind:value={settings.groq_model} onchange={save} /></label>
      <label>NVIDIA API Key <input type="password" bind:value={settings.nvidia_api_key} placeholder="••••" onchange={save} /></label>
      <label>FW Model <select bind:value={settings.fw_model} onchange={save}>
        <option>tiny</option><option>base</option><option>small</option><option>medium</option><option>large-v3</option>
      </select></label>
      <label>FW Device <select bind:value={settings.fw_device} onchange={save}>
        <option>auto</option><option>cpu</option><option>cuda</option>
      </select></label>
    </div>
    {/if}
  </section>

  <section class="panel-section">
    <button class="panel-header" onclick={() => toggle('audio')}>
      <span>🎵 Audio</span><span class="chevron">{expanded === 'audio' ? '▾' : '▸'}</span>
    </button>
    {#if expanded === 'audio'}
    <div class="panel-body">
      <label>Ruta audio <input bind:value={settings.audio_path} onchange={save} /></label>
      <label>Ruta transcripciones <input bind:value={settings.transcriptions_path} onchange={save} /></label>
      <label class="switch-label"><input type="checkbox" bind:checked={settings.save_audio} onchange={save} /> Guardar audio</label>
      <label>Max archivos <input type="number" bind:value={settings.max_files} onchange={save} /></label>
      <label class="switch-label"><input type="checkbox" bind:checked={settings.auto_cleanup} onchange={save} /> Auto-limpieza</label>
    </div>
    {/if}
  </section>

  <section class="panel-section">
    <button class="panel-header" onclick={() => toggle('recording')}>
      <span>⏺️ Grabación</span><span class="chevron">{expanded === 'recording' ? '▾' : '▸'}</span>
    </button>
    {#if expanded === 'recording'}
    <div class="panel-body">
      <label>Modo <select bind:value={settings.record_mode} onchange={save}>
        <option>toggle</option><option>hold</option>
      </select></label>
      <label>Tiempo máximo <select bind:value={settings.max_recording_time} onchange={save}>
        <option>5min</option><option>10min</option><option>15min</option><option>20min</option>
      </select></label>
    </div>
    {/if}
  </section>

  <section class="panel-section">
    <button class="panel-header" onclick={() => toggle('ui')}>
      <span>🖥️ Interfaz</span><span class="chevron">{expanded === 'ui' ? '▾' : '▸'}</span>
    </button>
    {#if expanded === 'ui'}
    <div class="panel-body">
      <label class="switch-label"><input type="checkbox" bind:checked={settings.auto_paste} onchange={save} /> Auto-pegar al portapapeles</label>
      <label class="switch-label"><input type="checkbox" bind:checked={settings.show_overlay} onchange={save} /> Mostrar overlay de grabación</label>
      <label class="switch-label"><input type="checkbox" bind:checked={settings.start_with_windows} onchange={save} /> Iniciar con Windows</label>
    </div>
    {/if}
  </section>

  <section class="panel-section">
    <button class="panel-header" onclick={() => toggle('post-processing')}>
      <span>🤖 Post-Procesamiento</span><span class="chevron">{expanded === 'post-processing' ? '▾' : '▸'}</span>
    </button>
    {#if expanded === 'post-processing'}
    <div class="panel-body">
      <label class="switch-label"><input type="checkbox" bind:checked={settings.post_process} onchange={save} /> Mejora con IA</label>
      <label>Modelo <input bind:value={settings.ai_model} onchange={save} /></label>
      <label>Perfil <select bind:value={settings.ai_profile} onchange={save}>
        <option>light</option><option>medium</option><option>aggressive</option>
      </select></label>
    </div>
    {/if}
  </section>

  <section class="panel-section">
    <button class="panel-header" onclick={() => toggle('blocks')}>
      <span>🧩 Bloques de Contexto</span><span class="chevron">{expanded === 'blocks' ? '▾' : '▸'}</span>
    </button>
    {#if expanded === 'blocks'}
    <div class="panel-body">
      <label class="switch-label"><input type="checkbox" bind:checked={settings.task_extractor} onchange={save} /> Extractor de Tareas</label>
      <label class="switch-label"><input type="checkbox" bind:checked={settings.summary} onchange={save} /> Resumen Automático</label>
      <label class="switch-label"><input type="checkbox" bind:checked={settings.keyword_extractor} onchange={save} /> Palabras Clave</label>
    </div>
    {/if}
  </section>

  <section class="panel-section">
    <button class="panel-header" onclick={() => toggle('hotkey')}>
      <span>⌨️ Hotkeys</span><span class="chevron">{expanded === 'hotkey' ? '▾' : '▸'}</span>
    </button>
    {#if expanded === 'hotkey'}
    <div class="panel-body">
      <label>Atajo de grabación <input bind:value={settings.hotkey} onchange={save} placeholder="Ctrl+Shift+R" /></label>
    </div>
    {/if}
  </section>

  <section class="panel-section">
    <button class="panel-header" onclick={() => toggle('vocabulary')}>
      <span>📝 Vocabulario Custom</span><span class="chevron">{expanded === 'vocabulary' ? '▾' : '▸'}</span>
    </button>
    {#if expanded === 'vocabulary'}
    <div class="panel-body">
      <p class="hint">Correcciones de palabras que el modelo entiende mal (ej: CENF → zenf). Configurable vía API.</p>
    </div>
    {/if}
  </section>
</div>

<style>
  .settings-view {
    padding: var(--dt-spacing-lg);
    max-width: 640px;
    display: flex;
    flex-direction: column;
    gap: var(--dt-spacing-sm);
  }
  .settings-header {
    display: flex;
    align-items: baseline;
    gap: var(--dt-spacing-md);
    margin-bottom: var(--dt-spacing-md);
    flex-wrap: wrap;
  }
  .settings-header h2 {
    margin: 0;
    font-size: var(--dt-font-size-xl);
    color: var(--dt-color-accent-default);
  }
  .saving-badge {
    font-size: var(--dt-font-size-xs);
    color: var(--dt-color-status-success);
  }
  .error-badge {
    font-size: var(--dt-font-size-xs);
    color: var(--dt-color-status-error, #ff6b6b);
  }
  .mock-badge {
    font-size: var(--dt-font-size-xs);
    background: var(--dt-color-bg-tertiary);
    color: var(--dt-color-text-secondary);
    padding: 2px 8px;
    border-radius: var(--dt-radius-sm);
  }
  .mock-info {
    font-size: var(--dt-font-size-sm);
    color: var(--dt-color-status-success, #4ade80);
    background: var(--dt-color-bg-tertiary);
    padding: var(--dt-spacing-sm);
    border-radius: var(--dt-radius-sm);
  }
  .warning-info {
    font-size: var(--dt-font-size-sm);
    color: var(--dt-color-status-warning, #facc15);
    background: var(--dt-color-bg-tertiary);
    padding: var(--dt-spacing-sm);
    border-radius: var(--dt-radius-sm);
  }
  .panel-section {
    background: var(--dt-color-bg-secondary);
    border-radius: var(--dt-radius-md);
    overflow: hidden;
  }
  .panel-header {
    width: 100%;
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: var(--dt-spacing-md) var(--dt-spacing-lg);
    background: transparent;
    border: none;
    color: var(--dt-color-text-primary);
    font-size: var(--dt-font-size-base);
    font-family: var(--dt-font-family);
    cursor: pointer;
  }
  .panel-header:hover { background: var(--dt-color-bg-hover); }
  .chevron { color: var(--dt-color-text-muted); }

  .panel-body {
    padding: var(--dt-spacing-md) var(--dt-spacing-lg);
    display: flex;
    flex-direction: column;
    gap: var(--dt-spacing-md);
    border-top: 1px solid var(--dt-color-border-default);
  }
  label {
    display: flex;
    flex-direction: column;
    gap: var(--dt-spacing-xs);
    font-size: var(--dt-font-size-sm);
    color: var(--dt-color-text-secondary);
  }
  input, select {
    padding: var(--dt-spacing-sm);
    background: var(--dt-color-bg-tertiary);
    border: 1px solid var(--dt-color-border-default);
    border-radius: var(--dt-radius-sm);
    color: var(--dt-color-text-primary);
    font-size: var(--dt-font-size-base);
    font-family: var(--dt-font-family);
  }
  .switch-label {
    flex-direction: row;
    align-items: center;
    gap: var(--dt-spacing-sm);
  }
  .hint {
    font-size: var(--dt-font-size-sm);
    color: var(--dt-color-text-muted);
  }
</style>
