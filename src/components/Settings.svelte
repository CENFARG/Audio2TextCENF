<script lang="ts">
  import { getConfig, saveConfig } from "../lib/commands";
  import { t } from "../lib/i18n.svelte";
  import { setLanguage, currentLanguage } from "../lib/i18n.svelte";

  interface VocabEntry {
    incorrect: string;
    correct: string;
  }

  let hotkey = $state("f9");
  let uiLanguage = $state(currentLanguage());
  let transcriptionLanguage = $state("es");
  let audioPath = $state("./audio");
  let transcriptionsPath = $state("./transcriptions");
  let vocab = $state<VocabEntry[]>([]);
  let newIncorrect = $state("");
  let newCorrect = $state("");
  let saveStatus = $state<"idle" | "saving" | "saved" | "error">("idle");

  // Config switches
  let autoPaste = $state(true);
  let showPanel = $state(false);
  let recordMode = $state("toggle");
  let groqApiKey = $state("");

  // Vocab import/export
  let importText = $state("");
  let exportText = $state("");
  let importStatus = $state<"idle" | "ok" | "error" | "empty">("idle");
  let importCount = $state(0);
  let copyStatus = $state<"idle" | "copied">("idle");

  // Refs for enter-to-add flow
  let incorrectInput = $state<HTMLInputElement | null>(null);
  let correctInput = $state<HTMLInputElement | null>(null);

  async function loadConfig(): Promise<void> {
    const response = await getConfig();
    if (response.status === "ok" && response.data) {
      const data = response.data as Record<string, unknown>;
      if (typeof data.hotkey === "string") hotkey = data.hotkey;
      if (typeof data.ui_language === "string") {
        uiLanguage = data.ui_language;
        setLanguage(data.ui_language);
      }
      if (typeof data.transcription_language === "string")
        transcriptionLanguage = data.transcription_language;
      if (typeof data.audio_path === "string") audioPath = data.audio_path;
      if (typeof data.transcriptions_path === "string")
        transcriptionsPath = data.transcriptions_path;
      if (Array.isArray(data.vocab_corrections))
        vocab = data.vocab_corrections as VocabEntry[];
      if (typeof data.auto_paste_text === "boolean") autoPaste = data.auto_paste_text;
      if (typeof data.show_transcription_panel === "boolean")
        showPanel = data.show_transcription_panel;
      if (typeof data.record_mode === "string") recordMode = data.record_mode;
      if (typeof data.groq_api_key === "string") groqApiKey = data.groq_api_key;
    }
  }

  async function handleSave(): Promise<void> {
    saveStatus = "saving";
    setLanguage(uiLanguage);
    const response = await saveConfig({
      hotkey,
      ui_language: uiLanguage,
      transcription_language: transcriptionLanguage,
      audio_path: audioPath,
      transcriptions_path: transcriptionsPath,
      vocab_corrections: vocab,
      auto_paste_text: autoPaste,
      show_transcription_panel: showPanel,
      record_mode: recordMode,
      groq_api_key: groqApiKey,
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
      incorrectInput?.focus();
    }
  }

  function removeVocab(index: number): void {
    vocab = vocab.filter((_, i) => i !== index);
  }

  function onIncorrectKeydown(e: KeyboardEvent): void {
    if (e.key === "Enter") {
      e.preventDefault();
      correctInput?.focus();
    }
  }

  function onCorrectKeydown(e: KeyboardEvent): void {
    if (e.key === "Enter") {
      e.preventDefault();
      addVocab();
    }
  }

  function importVocab(): void {
    const lines = importText.split("\n").filter((l) => l.trim());
    const parsed: VocabEntry[] = [];
    for (const line of lines) {
      const parts = line.split("=").map((s) => s.trim());
      if (parts.length === 2 && parts[0] && parts[1]) {
        parsed.push({ incorrect: parts[0], correct: parts[1] });
      }
    }
    if (parsed.length > 0) {
      vocab = [...vocab, ...parsed];
      importStatus = "ok";
      importCount = parsed.length;
      importText = "";
    } else {
      importStatus = "empty";
      importCount = 0;
    }
    setTimeout(() => {
      importStatus = "idle";
    }, 3000);
  }

  function prepareExport(): void {
    exportText = vocab.map((e) => `${e.incorrect} = ${e.correct}`).join("\n");
  }

  async function copyExport(): Promise<void> {
    try {
      await navigator.clipboard.writeText(exportText);
      copyStatus = "copied";
      setTimeout(() => {
        copyStatus = "idle";
      }, 2000);
    } catch {
      // fallback: select text
    }
  }

  $effect(() => {
    loadConfig();
  });

  $effect(() => {
    if (vocab.length > 0) {
      prepareExport();
    }
  });
</script>

<div class="settings">
  <h2>{t("tab_settings")}</h2>

  <section class="section">
    <h3>{t("language_label")}</h3>
    <label class="field">
      <span>{t("language_label")}</span>
      <select bind:value={uiLanguage} class="input">
        <option value="es">Español</option>
        <option value="en">English</option>
      </select>
    </label>
  </section>

  <section class="section">
    <h3>{t("settings_title_main")}</h3>

    <label class="field">
      <span>{t("hotkey_label")}</span>
      <input type="text" bind:value={hotkey} class="input" />
    </label>

    <label class="field">
      <span>{t("record_mode_label")}</span>
      <select bind:value={recordMode} class="input">
        <option value="toggle">{t("record_mode_toggle")}</option>
        <option value="hold">{t("record_mode_hold")}</option>
      </select>
    </label>

    <label class="field">
      <span>{t("api_key_placeholder")}</span>
      <input type="password" bind:value={groqApiKey} class="input" placeholder="gsk_..." />
    </label>

    <label class="switch-field">
      <span>{t("auto_paste_switch")}</span>
      <input type="checkbox" bind:checked={autoPaste} class="toggle" />
    </label>

    <label class="switch-field">
      <span>{t("show_panel_switch")}</span>
      <input type="checkbox" bind:checked={showPanel} class="toggle" />
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
        bind:this={incorrectInput}
        class="input"
        onkeydown={onIncorrectKeydown}
      />
      <input
        type="text"
        placeholder={t("vocab_correct_placeholder")}
        bind:value={newCorrect}
        bind:this={correctInput}
        class="input"
        onkeydown={onCorrectKeydown}
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

    <div class="vocab-io">
      <div class="vocab-io-section">
        <h4>{t("vocab_import_button")}</h4>
        <textarea
          class="vocab-textarea"
          placeholder={currentLanguage() === "es" ? "palabra incorrecta = palabra correcta\notra palabra = corrección" : "incorrect word = correct word\nanother word = correction"}
          bind:value={importText}
          rows="4"
        ></textarea>
        <button class="btn-small" onclick={importVocab} disabled={!importText.trim()}>
          {currentLanguage() === "es" ? "Importar" : "Import"}
        </button>
        {#if importStatus === "ok"}
          <span class="io-status ok">
            {currentLanguage() === "es" ? `${importCount} correcciones importadas` : `${importCount} corrections imported`}
          </span>
        {:else if importStatus === "empty"}
          <span class="io-status error">
            {currentLanguage() === "es" ? "Formato inválido (usar: palabra = corrección)" : "Invalid format (use: word = correction)"}
          </span>
        {/if}
      </div>

      <div class="vocab-io-section">
        <h4>{t("vocab_export_button")}</h4>
        <textarea
          class="vocab-textarea"
          readonly
          value={exportText}
          rows="4"
          placeholder={currentLanguage() === "es" ? "No hay vocabulario para exportar" : "No vocabulary to export"}
        ></textarea>
        <button class="btn-small" onclick={copyExport} disabled={!exportText}>
          {copyStatus === "copied" ? "✓" : (currentLanguage() === "es" ? "Copiar" : "Copy")}
        </button>
      </div>
    </div>
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

  .switch-field {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .switch-field span {
    font-size: 0.8rem;
    color: var(--text-secondary);
  }

  .toggle {
    width: 40px;
    height: 22px;
    accent-color: var(--accent);
    cursor: pointer;
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

  .btn-small:disabled {
    opacity: 0.5;
    cursor: not-allowed;
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

  .vocab-io {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 1rem;
    margin-top: 0.5rem;
  }

  .vocab-io-section {
    display: flex;
    flex-direction: column;
    gap: 0.4rem;
  }

  .vocab-io-section h4 {
    font-size: 0.8rem;
    color: var(--text-primary);
    margin: 0;
  }

  .vocab-textarea {
    padding: 0.5rem;
    border: 1px solid var(--border);
    border-radius: 6px;
    background: var(--bg-primary);
    color: var(--text-primary);
    font-size: 0.75rem;
    font-family: monospace;
    resize: vertical;
    outline: none;
  }

  .vocab-textarea:focus {
    border-color: var(--accent);
  }

  .io-status {
    font-size: 0.75rem;
  }

  .io-status.ok {
    color: var(--accent-green);
  }

  .io-status.error {
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
