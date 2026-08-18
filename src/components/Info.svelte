<script lang="ts">
  import { t } from "../lib/i18n.svelte";

  const appVersion = "2.0.0";
</script>

<div class="info">
  <h2>{t("tab_info")}</h2>

  <section class="section">
    <h3>Audio2Text CENF</h3>
    <p class="version">v{appVersion}</p>
    <p class="description">
      Herramienta de transcripción de audio con IA.
      Convierte voz a texto usando Groq Cloud (Whisper Large v3).
    </p>
  </section>

  <section class="section">
    <h3>Servicios</h3>
    <p class="description">
      Transcripción: <strong>Groq Cloud</strong> (Whisper Large v3)<br/>
      API: <a href="https://console.groq.com/keys" target="_blank" rel="noopener">console.groq.com/keys</a>
    </p>
  </section>

  <section class="section">
    <h3>Uso</h3>
    <ol class="usage-list">
      <li>Configura tu Hotkey (Default F9)</li>
      <li>Presiona para grabar, suelta o presiona de nuevo para terminar</li>
      <li>La transcripción se copia al portapapeles automáticamente</li>
    </ol>
  </section>

  <section class="section">
    <h3>Créditos</h3>
    <p class="description">
      <a href="https://www.cenfarg.com.ar" target="_blank" rel="noopener">www.cenfarg.com.ar</a>
    </p>
    <p class="disclaimer">
      ⚠️ Esta herramienta utiliza servicios de terceros (Groq) para procesar audio.
      No comparta información confidencial o sensible sin autorización.
      El usuario es responsable del contenido procesado.
    </p>
  </section>
</div>

<style>
  .info {
    display: flex;
    flex-direction: column;
    gap: 1.5rem;
    padding: 1.5rem;
    overflow-y: auto;
    height: 100%;
  }

  h2 {
    font-size: 1.2rem;
    color: var(--accent);
  }

  .section {
    display: flex;
    flex-direction: column;
    gap: 0.6rem;
    padding: 1rem;
    background: var(--bg-secondary);
    border: 1px solid var(--border);
    border-radius: 8px;
  }

  h3 {
    font-size: 0.95rem;
    color: var(--text-primary);
    margin-bottom: 0.2rem;
  }

  .version {
    font-size: 1.5rem;
    font-weight: 700;
    color: var(--accent);
  }

  .description {
    font-size: 0.8rem;
    color: var(--text-secondary);
    line-height: 1.5;
  }

  .description a {
    color: var(--accent);
    text-decoration: none;
  }

  .description a:hover {
    text-decoration: underline;
  }

  .usage-list {
    font-size: 0.8rem;
    color: var(--text-secondary);
    line-height: 1.8;
    padding-left: 1.2rem;
  }

  .disclaimer {
    font-size: 0.75rem;
    color: var(--text-secondary);
    font-style: italic;
    line-height: 1.5;
    margin-top: 0.5rem;
    opacity: 0.8;
  }
</style>
