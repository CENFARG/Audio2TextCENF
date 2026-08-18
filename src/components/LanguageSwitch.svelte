<script lang="ts">
  import { invoke } from "@tauri-apps/api/core";

  let transcriptionLanguage = $state("es");

  function toggle(): void {
    transcriptionLanguage = transcriptionLanguage === "es" ? "en" : "es";
    invoke("save_config", { config: { transcription_language: transcriptionLanguage } });
  }
</script>

<button class="lang-switch" onclick={toggle} title={transcriptionLanguage === "es" ? "Transcribir en Español" : "Transcribe in English"}>
  <span class="lang-label">Transcribir en:</span>
  <span class="lang-code" class:active={transcriptionLanguage === "es"}>ES</span>
  <span class="separator">/</span>
  <span class="lang-code" class:active={transcriptionLanguage === "en"}>EN</span>
</button>

<style>
  .lang-switch {
    display: flex;
    align-items: center;
    gap: 0.25rem;
    padding: 0.3rem 0.6rem;
    border: 1px solid var(--border);
    border-radius: 6px;
    background: var(--bg-secondary);
    cursor: pointer;
    font-size: 0.75rem;
    font-weight: 600;
  }

  .lang-switch:hover {
    border-color: var(--accent);
  }

  .lang-label {
    color: var(--text-secondary);
    font-weight: 400;
    margin-right: 0.2rem;
  }

  .lang-code {
    color: var(--text-secondary);
    transition: color 0.2s;
  }

  .lang-code.active {
    color: var(--accent);
  }

  .separator {
    color: var(--text-secondary);
  }
</style>
