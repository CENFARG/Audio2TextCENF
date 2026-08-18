<script lang="ts">
  import { getConfig, saveConfig } from "../lib/commands";
  import { t } from "../lib/i18n.svelte";
  import { setLanguage, currentLanguage } from "../lib/i18n.svelte";

  interface VocabEntry {
    incorrect: string;
    correct: string;
  }

  let hotkey = $state("f9");
  let language = $state(currentLanguage());
  let audioPath = $state("./audio");
  let transcriptionsPath = $state("./transcriptions");
  let vocab = $state<VocabEntry[]>([]);
  let newIncorrect = $state("");
  let newCorrect = $state("");
  let saveStatus = $state<"idle" | "saving" | "saved" | "error">("idle");

  async function loadConfig(): Promise<void> {
    const response = await getConfig();
    if (response.status === "ok" && response.data) {
      const data = response.data as Record<string, unknown>;
      if (typeof data.hotkey === "string") hotkey = data.hotkey;
      if (typeof data.ui_language === "string") {
        language = data.ui_language;
        setLanguage(data.ui_language);
      }
      if (typeof data.audio_path === "string") audioPath = data.audio_path;
      if (typeof data.transcriptions_path === "string")
        transcriptionsPath = data.transcriptions_path;
      if (Array.isArray(data.vocab_corrections)) {
        vocab = data.vocab_corrections as VocabEntry[];
      }
    }
  }

  async function handleSave(): Promise<void> {
    saveStatus = "saving";
    setLanguage(language);
    const response = await saveConfig({
      hotkey,
      ui_language: language,
      audio_path: audioPath,
      transcriptions_path: transcriptionsPath,
      vocab_corrections: vocab,
    });
    saveStatus = response.status === "ok" ? "saved" : "error";
    setTimeout(() => {
      saveStatus = "idle";
    }, 2000);
  }

  function addVocab(): void {
    if (newIncorrect.trim() && newCorrect.trim()) {
      vocab = [...vocab, { incorrect: newIncorrect.trim(), correct: newCorrect.trim() }];
      newIncorrect = "";
      newCorrect = "";
    }
  }

  function removeVocab(index: number): void {
    vocab = vocab.filter((_, i) => i !== index);
  }

  $effect(() => {
    loadConfig();
  });
</script>

<div class="settings">
  <h2>{t("tab_settings")}</h2>

  <section class="section">
    <h3>{t("settings_title_main")}</h3>

    <label class="field">
      <span>{t("hotkey_label")}</span>
      <input type="text" bind:value={hotkey} class="input" />
    </label>

    <label class="field">
      <span>{t("language_label")}</span>
      <select bind:value={language} class="input">
        <option value="es">Español</option>
        <option value="en">English</option>
      </select>
    </label>
  </section>

  <section class="section">
    <h3>{t("settings_title_files")}</h3>

    <label class="field">
      <span>{t("audio_path_label")}</span>
      <input type="text" bind:value={audioPath} class="input" />
    </label>

    <label class="field">
      <span>{t("transcriptions_path_label")}</span>
      <input type="text" bind:value={transcriptionsPath} class="input" />
    </label>
  </section>

  <section class="section">
    <h3>{t("vocab_title")}</h3>
    <p class="description">{t("vocab_description")}</p>

    <div class="vocab-add">
      <input
        type="text"
        placeholder={t("vocab_incorrect_placeholder")}
        bind:value={newIncorrect}
        class="input"
      />
      <input
        type="text"
        placeholder={t("vocab_correct_placeholder")}
        bind:value={newCorrect}
        class="input"
      />
      <button class="btn-small" onclick={addVocab}>{t("vocab_add_button")}</button>
    </div>

    {#if vocab.length === 0}
      <p class="empty">{t("vocab_empty")}</p>
    {:else}
      <ul class="vocab-list">
        {#each vocab as entry, i}
          <li class="vocab-item">
            <span class="incorrect">{entry.incorrect}</span>
            <span class="arrow">→</span>
            <span class="correct">{entry.correct}</span>
            <button class="remove-btn" onclick={() => removeVocab(i)}>×</button>
          </li>
        {/each}
      </ul>
    {/if}
  </section>

  <button
    class="save-btn"
    onclick={handleSave}
    disabled={saveStatus === "saving"}
  >
    {#if saveStatus === "saving"}
      ...
    {:else if saveStatus === "saved"}
      ✓
    {:else}
      {t("save_settings_button")}
    {/if}
  </button>
</div>

<style>
  .settings {
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
    gap: 0.8rem;
    padding: 1rem;
    background: var(--bg-secondary);
    border: 1px solid var(--border);
    border-radius: 8px;
  }

  h3 {
    font-size: 0.95rem;
    color: var(--text-primary);
    margin-bottom: 0.3rem;
  }

  .description {
    font-size: 0.8rem;
    color: var(--text-secondary);
  }

  .field {
    display: flex;
    flex-direction: column;
    gap: 0.3rem;
  }

  .field span {
    font-size: 0.8rem;
    color: var(--text-secondary);
  }

  .input {
    padding: 0.5rem 0.75rem;
    border: 1px solid var(--border);
    border-radius: 6px;
    background: var(--bg-primary);
    color: var(--text-primary);
    font-size: 0.85rem;
    outline: none;
  }

  .input:focus {
    border-color: var(--accent);
  }

  .vocab-add {
    display: flex;
    gap: 0.5rem;
    align-items: center;
  }

  .vocab-add .input {
    flex: 1;
  }

  .btn-small {
    padding: 0.5rem 0.8rem;
    font-size: 0.8rem;
    border: 1px solid var(--accent);
    border-radius: 6px;
    background: transparent;
    color: var(--accent);
    cursor: pointer;
    white-space: nowrap;
  }

  .btn-small:hover {
    background: var(--accent);
    color: var(--bg-primary);
  }

  .empty {
    font-size: 0.8rem;
    color: var(--text-secondary);
    font-style: italic;
  }

  .vocab-list {
    list-style: none;
    display: flex;
    flex-direction: column;
    gap: 0.3rem;
  }

  .vocab-item {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.4rem 0.6rem;
    background: var(--bg-primary);
    border-radius: 4px;
    font-size: 0.8rem;
  }

  .incorrect {
    color: #ff6666;
    text-decoration: line-through;
  }

  .arrow {
    color: var(--text-secondary);
  }

  .correct {
    color: var(--accent-green);
  }

  .remove-btn {
    margin-left: auto;
    background: none;
    border: none;
    color: var(--text-secondary);
    cursor: pointer;
    font-size: 1rem;
  }

  .remove-btn:hover {
    color: #ff4444;
  }

  .save-btn {
    padding: 0.7rem 1.5rem;
    font-size: 0.9rem;
    font-weight: 600;
    border: none;
    border-radius: 8px;
    background: var(--accent);
    color: var(--bg-primary);
    cursor: pointer;
    align-self: flex-start;
    transition: filter 0.2s;
  }

  .save-btn:hover {
    filter: brightness(1.1);
  }

  .save-btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
</style>
