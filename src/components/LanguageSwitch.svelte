<script lang="ts">
  import { currentLanguage, setLanguage } from "../lib/i18n";

  let lang = $derived(currentLanguage());

  function toggle(): void {
    setLanguage(lang === "es" ? "en" : "es");
  }
</script>

<button class="lang-switch" onclick={toggle} title={lang === "es" ? "Switch to English" : "Cambiar a Español"}>
  <span class="lang-code" class:active={lang === "es"}>ES</span>
  <span class="separator">/</span>
  <span class="lang-code" class:active={lang === "en"}>EN</span>
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
