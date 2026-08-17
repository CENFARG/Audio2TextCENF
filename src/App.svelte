<script lang="ts">
  let version = $state("2.0.0");
  let status = $state("idle");
</script>

<main class="container">
  <h1>Audio2Text v{version}</h1>
  <p class="subtitle">Tauri 2 + Svelte 5</p>

  <div class="status-card">
    <span class="status-dot" class:active={status === "recording"}></span>
    <span>Status: {status}</span>
  </div>

  <p class="placeholder">UI coming in Phase 3</p>
</main>

<style>
  .container {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    min-height: 100vh;
    padding: 2rem;
    font-family: system-ui, -apple-system, sans-serif;
    background: #1a1a2e;
    color: #e0e0e0;
  }

  h1 {
    font-size: 2rem;
    margin-bottom: 0.5rem;
    color: #00d4ff;
  }

  .subtitle {
    font-size: 1rem;
    color: #888;
    margin-bottom: 2rem;
  }

  .status-card {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 1rem 1.5rem;
    background: #16213e;
    border-radius: 8px;
    border: 1px solid #0f3460;
  }

  .status-dot {
    width: 10px;
    height: 10px;
    border-radius: 50%;
    background: #555;
  }

  .status-dot.active {
    background: #00ff88;
    box-shadow: 0 0 8px #00ff8866;
  }

  .placeholder {
    margin-top: 2rem;
    color: #666;
    font-style: italic;
  }
</style>
